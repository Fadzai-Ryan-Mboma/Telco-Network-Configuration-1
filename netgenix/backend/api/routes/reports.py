"""Reporting automation API endpoints."""

import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from backend.models.schemas import (
    ReportColumnPreviewResponse,
    ReportFormulaPreviewRequest,
    ReportFormulaPreviewResponse,
    ReportRunSummary,
    ReportRunResponse,
    ReportAutomationJob,
    ReportAutomationRequest,
    ReportExclusions,
)
from backend.netgenix.reports.engine import (
    average_gb_per_active_user,
    average_throughput_per_active_user,
    code_drop_average,
    get_report_output_path,
    get_report_pdf_path,
    list_report_runs,
    penetration_rate,
    preview_column_mapping,
    prb_busy_hour_weekly_average,
    run_report_from_file,
    run_report_from_files,
    weekly_traffic_total_gb,
    weekly_traffic_total_tb,
)
from backend.netgenix.services.report_automation import (
    create_job,
    get_exclusions,
    get_job,
    list_jobs,
    replace_exclusions,
)

router = APIRouter()


@router.post(
    "/automation/runs",
    response_model=ReportAutomationJob,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_automation_run(request: ReportAutomationRequest):
    """Start a fresh Evaluation pull or generate from existing database data."""
    try:
        return create_job(
            request.period_start,
            request.period_end,
            refresh=request.refresh,
            exclusion_overrides=request.exclusion_overrides,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/automation/runs/{job_id}", response_model=ReportAutomationJob)
async def get_automation_run(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Automation job '{job_id}' not found")
    return job


@router.get("/automation/runs", response_model=list[ReportAutomationJob])
async def list_automation_runs(limit: int = Query(10, ge=1, le=50)):
    return list_jobs(limit)


@router.get("/exclusions", response_model=ReportExclusions)
async def read_report_exclusions():
    return {"sites": get_exclusions()}


@router.put("/exclusions", response_model=ReportExclusions)
async def write_report_exclusions(request: ReportExclusions):
    return {"sites": replace_exclusions(request.sites)}


@router.post("/formulas/preview", response_model=ReportFormulaPreviewResponse)
async def preview_report_formulas(request: ReportFormulaPreviewRequest):
    """Preview deterministic v2 reporting formulas before Excel generation."""
    weekly_gb = weekly_traffic_total_gb(request.daily_traffic_gb)

    return ReportFormulaPreviewResponse(
        weekly_traffic_gb=weekly_gb,
        weekly_traffic_tb=weekly_traffic_total_tb(request.daily_traffic_gb),
        prb_busy_hour_weekly_average=prb_busy_hour_weekly_average(request.prb_busy_hour_values),
        code_drop_average=code_drop_average(request.code_drop_values),
        penetration_rate=penetration_rate(
            request.active_subscribers,
            request.addressable_subscribers,
        ),
        average_gb_per_active_user=average_gb_per_active_user(
            weekly_gb,
            request.active_subscribers,
        ),
        average_throughput_per_active_user=average_throughput_per_active_user(
            request.total_throughput_mbps,
            request.active_subscribers,
        ),
    )


@router.post("/imports", response_model=ReportRunResponse)
async def import_report_file(
    file: UploadFile = File(...),
    exclusions: str = Query("", description="Comma-separated site names to exclude from rankings"),
    user_context: str = Query("local", description="Operator/session context for audit trail"),
):
    """Import a CSV/XLSX export, compute v2 metrics, and generate downloadable Excel."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xlsm", ".xltx", ".xltm"}:
        raise HTTPException(status_code=400, detail="Only CSV and Excel inputs are supported")

    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = Path(temp_file.name)

    try:
        exclusion_list = [site.strip() for site in exclusions.split(",") if site.strip()]
        result = run_report_from_file(
            temp_path,
            original_filename=file.filename or f"input{suffix}",
            exclusions=exclusion_list,
            user_context=user_context,
        )
    except Exception as error:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Report import failed: {error}") from error

    return ReportRunResponse(
        run_id=str(result["run_id"]),
        status="success",
        input_file=str(result["input_file"]),
        output_file=str(result["output_file"]),
        download_url=f"/api/reports/runs/{result['run_id']}/download",
        pdf_file=str(result["pdf_file"]),
        pdf_download_url=f"/api/reports/runs/{result['run_id']}/download/pdf",
        site_count=int(result["site_count"]),
        sections=result["sections"],
        top_traffic_sites=result["top_traffic_sites"],
        bottom_traffic_sites=result["bottom_traffic_sites"],
        audit_file=str(result["audit_file"]),
    )


@router.post("/cook", response_model=ReportRunResponse)
async def cook_report_files(
    files: list[UploadFile] = File(...),
    exclusions: str = Query("", description="Comma-separated site names to exclude from rankings"),
    user_context: str = Query("local", description="Operator/session context for audit trail"),
):
    """Cook multiple raw exports into one Brighton-parity workbook."""
    if not files:
        raise HTTPException(status_code=400, detail="At least one CSV or Excel input is required")

    temp_files: list[tuple[Path, str]] = []
    try:
        for file in files:
            suffix = Path(file.filename or "").suffix.lower()
            if suffix not in {".csv", ".xlsx", ".xlsm", ".xltx", ".xltm"}:
                raise HTTPException(status_code=400, detail=f"Unsupported input type for {file.filename}")

            with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                temp_path = Path(temp_file.name)
            temp_files.append((temp_path, file.filename or f"input{suffix}"))

        exclusion_list = [site.strip() for site in exclusions.split(",") if site.strip()]
        result = run_report_from_files(
            temp_files,
            exclusions=exclusion_list,
            user_context=user_context,
        )
    except HTTPException:
        for temp_path, _ in temp_files:
            temp_path.unlink(missing_ok=True)
        raise
    except Exception as error:
        for temp_path, _ in temp_files:
            temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Report cooking failed: {error}") from error

    return ReportRunResponse(
        run_id=str(result["run_id"]),
        status="success",
        input_file=str(result["input_file"]),
        output_file=str(result["output_file"]),
        download_url=f"/api/reports/runs/{result['run_id']}/download",
        pdf_file=str(result["pdf_file"]),
        pdf_download_url=f"/api/reports/runs/{result['run_id']}/download/pdf",
        site_count=int(result["site_count"]),
        sections=result["sections"],
        top_traffic_sites=result["top_traffic_sites"],
        bottom_traffic_sites=result["bottom_traffic_sites"],
        audit_file=str(result["audit_file"]),
    )


@router.post("/preview", response_model=ReportColumnPreviewResponse)
async def preview_report_file(file: UploadFile = File(...)):
    """Preview source columns and detected mappings before generating a report."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xlsm", ".xltx", ".xltm"}:
        raise HTTPException(status_code=400, detail="Only CSV and Excel inputs are supported")

    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = Path(temp_file.name)

    try:
        return preview_column_mapping(
            temp_path,
            original_filename=file.filename or f"input{suffix}",
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Report preview failed: {error}") from error
    finally:
        temp_path.unlink(missing_ok=True)


@router.get("/runs", response_model=list[ReportRunSummary])
async def get_report_runs():
    """List generated report runs."""
    return list_report_runs()


@router.get("/runs/{run_id}/download")
async def download_report(run_id: str):
    """Download a generated NetGenix Excel report."""
    output_path = get_report_output_path(run_id)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail=f"Report run '{run_id}' not found")

    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"netgenix_report_{run_id}.xlsx",
    )


@router.get("/runs/{run_id}/download/pdf")
async def download_pdf_report(run_id: str):
    """Download a generated NetGenix executive PDF report."""
    output_path = get_report_pdf_path(run_id)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail=f"PDF report run '{run_id}' not found")

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename=f"netgenix_report_{run_id}.pdf",
    )
