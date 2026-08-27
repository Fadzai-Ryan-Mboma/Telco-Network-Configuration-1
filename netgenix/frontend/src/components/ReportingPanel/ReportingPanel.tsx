import { useEffect, useState } from 'react';
import {
  AlertCircle,
  CalendarClock,
  CalendarDays,
  Database,
  Download,
  FileText,
  FileSpreadsheet,
  History,
  Layers,
  Link2,
  RefreshCw,
  Save,
  ShieldCheck,
  UploadCloud,
} from 'lucide-react';
import {
  cancelEvaluationReconnect,
  cookReportFiles,
  getAutomatedReportJobs,
  getAutomatedReportJob,
  getEvaluationReconnectStatus,
  getEvaluationStatus,
  getReportDownloadUrl,
  getReportExclusions,
  getReportRuns,
  previewReportFile,
  saveReportExclusions,
  startAutomatedReport,
  startEvaluationReconnect,
} from '../../services/api';
import type {
  EvaluationStatus,
  ReconnectSessionStatus,
  ReportAutomationJob,
  ReportColumnPreview,
  ReportRun,
  ReportRunSummary,
} from '../../services/api';

function defaultPeriod() {
  const today = new Date();
  const end = new Date(today);
  const daysSinceWednesday = (today.getDay() - 3 + 7) % 7 || 7;
  end.setDate(today.getDate() - daysSinceWednesday);
  const start = new Date(end);
  start.setDate(end.getDate() - 6);
  const iso = (value: Date) => value.toISOString().slice(0, 10);
  return { start: iso(start), end: iso(end) };
}

// Mirrors the daily rolling window used by the collector's daily_rolling_report
// cron job (network/evaluation_exporter.py: default_daily_rolling_period) —
// the most recently completed 7-day window ending yesterday.
function dailyRollingPeriod() {
  const today = new Date();
  const end = new Date(today);
  end.setDate(today.getDate() - 1);
  const start = new Date(end);
  start.setDate(end.getDate() - 6);
  const iso = (value: Date) => value.toISOString().slice(0, 10);
  return { start: iso(start), end: iso(end) };
}

export default function ReportingPanel() {
  const initialPeriod = defaultPeriod();
  const [files, setFiles] = useState<File[]>([]);
  const [exclusions, setExclusions] = useState('');
  const [savedExclusions, setSavedExclusions] = useState('');
  const [periodStart, setPeriodStart] = useState(initialPeriod.start);
  const [periodEnd, setPeriodEnd] = useState(initialPeriod.end);
  const [evaluation, setEvaluation] = useState<EvaluationStatus | null>(null);
  const [automationJob, setAutomationJob] = useState<ReportAutomationJob | null>(null);
  const [automationLoading, setAutomationLoading] = useState(false);
  const [savingExclusions, setSavingExclusions] = useState(false);
  const [reportRun, setReportRun] = useState<ReportRun | null>(null);
  const [preview, setPreview] = useState<ReportColumnPreview | null>(null);
  const [history, setHistory] = useState<ReportRunSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loadingFormat, setLoadingFormat] = useState<'excel' | 'pdf' | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [reconnectSession, setReconnectSession] = useState<ReconnectSessionStatus | null>(null);
  const [reconnectLoading, setReconnectLoading] = useState(false);

  async function loadHistory() {
    const runs = await getReportRuns();
    setHistory(runs);
  }

  useEffect(() => {
    loadHistory().catch(() => setHistory([]));
    getEvaluationStatus().then(setEvaluation).catch(() => setEvaluation(null));
    getReportExclusions().then((sites) => setSavedExclusions(sites.join(', '))).catch(() => undefined);
    getAutomatedReportJobs(1).then((jobs) => setAutomationJob(jobs[0] ?? null)).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!automationJob || !['queued', 'running'].includes(automationJob.status)) return;
    const timer = window.setInterval(async () => {
      try {
        const job = await getAutomatedReportJob(automationJob.job_id);
        setAutomationJob(job);
        if (job.status === 'completed') {
          await loadHistory();
          setEvaluation(await getEvaluationStatus());
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Could not read report status.');
      }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [automationJob?.job_id, automationJob?.status]);

  useEffect(() => {
    if (!reconnectSession || !['starting', 'awaiting_login'].includes(reconnectSession.status)) return;
    const timer = window.setInterval(async () => {
      try {
        const session = await getEvaluationReconnectStatus(reconnectSession.session_id);
        setReconnectSession(session);
        if (session.status === 'session_saved') {
          setEvaluation(await getEvaluationStatus());
        } else if (session.status === 'failed' || session.status === 'timeout') {
          setError(session.error_message ?? 'Evaluation reconnect did not complete.');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Could not read reconnect status.');
      }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [reconnectSession?.session_id, reconnectSession?.status]);

  useEffect(() => {
    return () => {
      if (reconnectSession && ['starting', 'awaiting_login'].includes(reconnectSession.status)) {
        cancelEvaluationReconnect(reconnectSession.session_id).catch(() => undefined);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleReconnect() {
    setReconnectLoading(true);
    setError(null);
    try {
      const session = await startEvaluationReconnect();
      setReconnectSession(session);
      if (session.novnc_url) {
        window.open(session.novnc_url, '_blank', 'noopener,noreferrer');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start Evaluation reconnect.');
    } finally {
      setReconnectLoading(false);
    }
  }

  async function handleAutomation(refresh: boolean, overridePeriod?: { start: string; end: string }) {
    const start = overridePeriod?.start ?? periodStart;
    const end = overridePeriod?.end ?? periodEnd;
    if (overridePeriod) {
      setPeriodStart(overridePeriod.start);
      setPeriodEnd(overridePeriod.end);
    }
    setAutomationLoading(true);
    setError(null);
    try {
      const overrides = exclusions.split(',').map((site) => site.trim()).filter(Boolean);
      setAutomationJob(await startAutomatedReport(start, end, refresh, overrides));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start the report.');
    } finally {
      setAutomationLoading(false);
    }
  }

  function handleRunDailyReportNow() {
    handleAutomation(true, dailyRollingPeriod());
  }

  async function handleSaveExclusions() {
    setSavingExclusions(true);
    setError(null);
    try {
      const sites = savedExclusions.split(',').map((site) => site.trim()).filter(Boolean);
      setSavedExclusions((await saveReportExclusions(sites)).join(', '));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save exclusions.');
    } finally {
      setSavingExclusions(false);
    }
  }

  async function handleFileChange(nextFiles: File[]) {
    setFiles(nextFiles);
    setPreview(null);
    setError(null);

    if (nextFiles.length === 0) {
      return;
    }

    setPreviewLoading(true);
    try {
      setPreview(await previewReportFile(nextFiles[0]));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Column preview failed.');
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleImport(preferredOutput: 'excel' | 'pdf') {
    if (files.length === 0) {
      setError('Choose at least one CSV or Excel export first.');
      return;
    }

    setLoadingFormat(preferredOutput);
    setError(null);
    try {
      const result = await cookReportFiles(files, exclusions);
      setReportRun(result);
      await loadHistory();
      if (preferredOutput === 'pdf') {
        window.open(getReportDownloadUrl(result.pdf_download_url), '_blank', 'noopener,noreferrer');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Report import failed.');
    } finally {
      setLoadingFormat(null);
    }
  }

  return (
    <div className="min-w-0 max-w-full space-y-6 overflow-x-hidden">
      <section className="border-b border-white/10 pb-6">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-white">Automated Evaluation Report</h3>
            <p className="mt-1 text-sm text-gray-400">Seven-day network and site performance report</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className={`badge ${evaluation?.connected ? 'badge-success' : 'badge-error'}`}>
              <ShieldCheck className="mr-1 h-3.5 w-3.5" />
              {evaluation?.connected ? 'Evaluation connected' : 'Re-authentication required'}
            </div>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleReconnect}
              disabled={reconnectLoading || (reconnectSession?.status === 'starting' || reconnectSession?.status === 'awaiting_login')}
              title="Opens a live view of the Evaluation login in a new tab. Complete the login (including CAPTCHA) there — the session is captured automatically once you finish."
            >
              <Link2 className="h-4 w-4" />
              <span>Reconnect</span>
            </button>
            {reconnectSession && ['starting', 'awaiting_login'].includes(reconnectSession.status) && (
              <span className="text-xs text-gray-500">Waiting for login in the reconnect tab…</span>
            )}
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <label className="text-xs text-gray-500">
            Period start
            <span className="input mt-1 flex items-center gap-2">
              <CalendarDays className="h-4 w-4 text-accent-teal" />
              <input className="min-w-0 flex-1 bg-transparent text-sm text-white outline-none" type="date" value={periodStart} onChange={(event) => setPeriodStart(event.target.value)} />
            </span>
          </label>
          <label className="text-xs text-gray-500">
            Period end
            <span className="input mt-1 flex items-center gap-2">
              <CalendarDays className="h-4 w-4 text-accent-teal" />
              <input className="min-w-0 flex-1 bg-transparent text-sm text-white outline-none" type="date" value={periodEnd} onChange={(event) => setPeriodEnd(event.target.value)} />
            </span>
          </label>
          <label className="text-xs text-gray-500 md:col-span-2">
            Per-run exclusion overrides
            <input className="input mt-1 w-full" value={exclusions} onChange={(event) => setExclusions(event.target.value)} placeholder="Site names, comma-separated" />
          </label>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button className="btn-primary" onClick={() => handleAutomation(true)} disabled={automationLoading || automationJob?.status === 'running'}>
            <RefreshCw className={`h-4 w-4 ${automationJob?.status === 'running' ? 'animate-spin' : ''}`} />
            <span>Refresh &amp; Generate</span>
          </button>
          <button className="btn-secondary" onClick={() => handleAutomation(false)} disabled={automationLoading || automationJob?.status === 'running'}>
            <Database className="h-4 w-4" />
            <span>Generate from Latest</span>
          </button>
          <button
            className="btn-secondary"
            onClick={handleRunDailyReportNow}
            disabled={automationLoading || automationJob?.status === 'running'}
            title="Refresh and generate a report for the most recently completed 7-day window (same window the daily automation uses)"
          >
            <CalendarClock className="h-4 w-4" />
            <span>Run Daily Report Now</span>
          </button>
          <span className="text-xs text-gray-500">
            Last extract: {evaluation?.last_successful_extraction ? new Date(evaluation.last_successful_extraction).toLocaleString() : 'None'}
          </span>
        </div>

        <div className="mt-4 flex gap-2">
          <input className="input min-w-0 flex-1" value={savedExclusions} onChange={(event) => setSavedExclusions(event.target.value)} placeholder="Saved non-commercial site exclusions" />
          <button className="btn-secondary" onClick={handleSaveExclusions} disabled={savingExclusions} title="Save exclusions">
            <Save className="h-4 w-4" />
            <span>Save</span>
          </button>
        </div>

        {automationJob && (
          <div className={`mt-4 border-l-2 px-3 py-2 ${automationJob.status === 'failed' ? 'border-status-error bg-status-error/5' : 'border-accent-teal bg-accent-teal/5'}`}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium capitalize text-white">{automationJob.stage.replaceAll('_', ' ')}</p>
                <p className="text-xs text-gray-500">Job {automationJob.job_id.slice(0, 8)} · {automationJob.period_start} to {automationJob.period_end}</p>
              </div>
              {automationJob.status === 'completed' && automationJob.download_url && automationJob.pdf_download_url && (
                <div className="flex gap-2">
                  <a className="btn-primary" href={getReportDownloadUrl(automationJob.download_url)}><Download className="h-4 w-4" /><span>Excel</span></a>
                  <a className="btn-secondary" href={getReportDownloadUrl(automationJob.pdf_download_url)}><FileText className="h-4 w-4" /><span>PDF</span></a>
                </div>
              )}
            </div>
            {automationJob.error_message && (
              <p className="mt-2 flex items-center gap-2 text-sm text-status-error"><AlertCircle className="h-4 w-4" />{automationJob.error_message}</p>
            )}
            {automationJob.status === 'failed' && automationJob.refresh_requested && (
              <button className="mt-3 text-sm font-medium text-accent-teal hover:underline" onClick={() => handleAutomation(false)}>Generate from latest successful extract</button>
            )}
          </div>
        )}
      </section>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 rounded-xl border border-white/5 bg-bg-input p-4">
          <div className="mb-4 flex items-center gap-3">
            <div className="rounded-lg bg-accent-teal/15 p-2">
              <FileSpreadsheet className="h-5 w-5 text-accent-teal" />
            </div>
            <div>
              <h3 className="font-semibold text-white">Manual Report Cooker</h3>
              <p className="text-sm text-gray-500">Upload manually extracted Evaluation export.</p>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <label className="input flex cursor-pointer items-center gap-3">
              <UploadCloud className="h-4 w-4 text-accent-teal" />
              <span className="truncate text-sm">
                {files.length > 0 ? `${files.length} file(s) selected` : 'Choose raw CSV/XLSX files'}
              </span>
              <input
                className="hidden"
                type="file"
                multiple
                accept=".csv,.xlsx,.xlsm,.xltx,.xltm"
                onChange={(event) => handleFileChange(Array.from(event.target.files ?? []))}
              />
            </label>
            <input
              className="input"
              value={exclusions}
              onChange={(event) => setExclusions(event.target.value)}
              placeholder="Excluded sites, comma-separated"
            />
          </div>

          {error && <p className="mt-3 text-sm text-status-error">{error}</p>}

          <div className="mt-4 flex flex-wrap gap-3">
            <button className="btn-primary" onClick={() => handleImport('excel')} disabled={loadingFormat !== null}>
              <Layers className="h-4 w-4" />
              <span>{loadingFormat === 'excel' ? 'Producing...' : 'Produce Excel Report'}</span>
            </button>
            <button className="btn-secondary" onClick={() => handleImport('pdf')} disabled={loadingFormat !== null}>
              <FileText className="h-4 w-4" />
              <span>{loadingFormat === 'pdf' ? 'Producing...' : 'Produce PDF Report'}</span>
            </button>
          </div>

          {files.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {files.map((selectedFile) => (
                <span key={`${selectedFile.name}-${selectedFile.size}`} className="badge badge-success">
                  {selectedFile.name}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-xl border border-white/5 bg-bg-input p-4">
          <p className="text-xs uppercase tracking-wide text-gray-500">Report Output</p>
          <h3 className="mt-2 text-lg font-semibold text-white">Excel and PDF reports</h3>
          <p className="mt-2 text-sm text-gray-400">
            Generate audit-ready Excel plus a styled executive PDF with KPIs, insights, rankings, and watchlists.
          </p>
          <div className="mt-4 space-y-2 text-sm text-gray-300">
            <a className="block text-accent-teal hover:underline" href="/samples/reports/evaluation_sample.csv">
              Evaluation sample CSV
            </a>
            <a className="block text-accent-teal hover:underline" href="/samples/reports/telrad_sample.csv">
              Telrad sample CSV
            </a>
            <a className="block text-accent-teal hover:underline" href="/samples/reports/epc_subscriber_sample.csv">
              EPC/subscriber sample CSV
            </a>
          </div>
        </div>
      </div>

      <ColumnPreview preview={preview} loading={previewLoading} />

      {reportRun && (
        <div className="rounded-xl border border-white/5 bg-bg-input p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="font-semibold text-white">Report Run {reportRun.run_id}</h3>
              <p className="text-sm text-gray-500">{reportRun.site_count} sites processed</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <a className="btn-primary" href={getReportDownloadUrl(reportRun.download_url)}>
                <Download className="h-4 w-4" />
                <span>Download Excel</span>
              </a>
              <a className="btn-secondary" href={getReportDownloadUrl(reportRun.pdf_download_url)}>
                <FileText className="h-4 w-4" />
                <span>Download PDF</span>
              </a>
            </div>
          </div>

          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            <RankingTable title="Top Traffic Sites" rows={reportRun.top_traffic_sites} />
            <RankingTable title="Bottom Traffic Sites" rows={reportRun.bottom_traffic_sites} />
          </div>

          <div className="mt-5">
            <h4 className="mb-3 font-medium text-white">Generated Report Sections</h4>
            <div className="grid gap-3 md:grid-cols-2">
              {reportRun.sections.map((section) => (
                <div key={section.worksheet} className="rounded-lg border border-white/5 bg-bg-card-hover p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-white">{section.name}</p>
                      <p className="text-xs text-accent-teal">{section.worksheet}</p>
                    </div>
                    <span className="badge badge-success">{section.status}</span>
                  </div>
                  <p className="mt-2 text-sm text-gray-400">{section.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <ReportHistory history={history} />
    </div>
  );
}

function ColumnPreview({ preview, loading }: { preview: ReportColumnPreview | null; loading: boolean }) {
  if (loading) {
    return <div className="rounded-xl border border-white/5 bg-bg-input p-4 text-sm text-gray-400">Reading columns...</div>;
  }

  if (!preview) {
    return null;
  }

  return (
    <div className="rounded-xl border border-white/5 bg-bg-input p-4">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold text-white">Column Mapping Preview</h3>
          <p className="text-sm text-gray-500">{preview.filename} · {preview.row_count} rows</p>
        </div>
        {preview.warnings.length > 0 ? (
          <span className="badge badge-warning">{preview.warnings.length} warning(s)</span>
        ) : (
          <span className="badge badge-success">Ready</span>
        )}
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {preview.mappings.map((mapping) => (
          <div key={mapping.concept} className="rounded-lg border border-white/5 bg-bg-card-hover p-3">
            <p className="text-xs uppercase tracking-wide text-gray-500">{mapping.concept.replaceAll('_', ' ')}</p>
            <p className="mt-1 font-medium text-white">{mapping.matched_column ?? 'Not detected'}</p>
            <span className={`badge mt-2 inline-block ${mapping.matched_column ? 'badge-success' : mapping.required ? 'badge-error' : 'badge-warning'}`}>
              {mapping.matched_column ? 'mapped' : mapping.required ? 'required' : 'optional'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ReportHistory({ history }: { history: ReportRunSummary[] }) {
  return (
    <div className="rounded-xl border border-white/5 bg-bg-input p-4">
      <div className="mb-4 flex items-center gap-3">
        <History className="h-5 w-5 text-accent-teal" />
        <div>
          <h3 className="font-semibold text-white">Report History</h3>
          <p className="text-sm text-gray-500">Previous generated workbooks and audit runs.</p>
        </div>
      </div>

      <div className="max-w-full overflow-x-auto rounded-lg border border-white/5">
        <table className="min-w-[720px] w-full text-left text-sm">
          <thead className="bg-bg-card-hover text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-3 py-2">Run</th>
              <th className="px-3 py-2">Source</th>
              <th className="px-3 py-2">Sites</th>
              <th className="px-3 py-2">Sections</th>
              <th className="px-3 py-2">Download</th>
              <th className="px-3 py-2">PDF</th>
            </tr>
          </thead>
          <tbody>
            {history.map((run) => (
              <tr key={run.run_id} className="border-t border-white/5 text-gray-300">
                <td className="px-3 py-2">{run.run_id}</td>
                <td className="px-3 py-2">{run.original_filename ?? 'Unknown'}</td>
                <td className="px-3 py-2">{run.site_count}</td>
                <td className="px-3 py-2">{run.sections_count}</td>
                <td className="px-3 py-2">
                  <a className="text-accent-teal hover:underline" href={getReportDownloadUrl(run.download_url)}>
                    Excel
                  </a>
                </td>
                <td className="px-3 py-2">
                  {run.pdf_download_url ? (
                    <a className="text-accent-teal hover:underline" href={getReportDownloadUrl(run.pdf_download_url)}>
                      PDF
                    </a>
                  ) : (
                    <span className="text-gray-500">-</span>
                  )}
                </td>
              </tr>
            ))}
            {history.length === 0 && (
              <tr>
                <td className="px-3 py-4 text-gray-500" colSpan={6}>No reports generated yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RankingTable({ title, rows }: { title: string; rows: ReportRun['top_traffic_sites'] }) {
  return (
    <div>
      <h4 className="mb-3 font-medium text-white">{title}</h4>
      <div className="overflow-hidden rounded-lg border border-white/5">
        <table className="w-full text-left text-sm">
          <thead className="bg-bg-card-hover text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-3 py-2">Site</th>
              <th className="px-3 py-2">GB</th>
              <th className="px-3 py-2">PRB</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.site_name} className="border-t border-white/5 text-gray-300">
                <td className="px-3 py-2">{row.site_name}</td>
                <td className="px-3 py-2">{row.weekly_traffic_gb.toFixed(2)}</td>
                <td className="px-3 py-2">{row.prb_busy_hour_weekly_average.toFixed(2)}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td className="px-3 py-4 text-gray-500" colSpan={3}>No ranking data yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
