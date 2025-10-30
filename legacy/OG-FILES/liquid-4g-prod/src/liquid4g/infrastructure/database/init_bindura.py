"""
Initialize database with real Bindura cluster sites
"""

from liquid4g.infrastructure.database.connection import get_db
from liquid4g.core.logging import get_logger
from datetime import datetime

logger = get_logger(__name__)

def initialize_bindura_sites():
    """Initialize database with real Bindura cluster network sites"""
    
    db = get_db()
    
    # Real Bindura cluster sites from the image
    bindura_sites = [
        {
            "site_id": "MSH-0013",
            "site_name": "MSH-0013-Bindura-Zaoga",
            "location": "Bindura-Zaoga",
            "latitude": -17.2985,
            "longitude": 31.3251,
            "region": "Bindura",
            "status": "active"
        },
        {
            "site_id": "MSH-0331",
            "site_name": "MSH-0331-Chiwaridzo 2", 
            "location": "Chiwaridzo 2",
            "latitude": -17.3025,
            "longitude": 31.3321,
            "region": "Bindura",
            "status": "active"
        },
        {
            "site_id": "MSH-0112",
            "site_name": "MSH-0112-Bindura Hospital",
            "location": "Bindura Hospital",
            "latitude": -17.3011,
            "longitude": 31.3297,
            "region": "Bindura", 
            "status": "active"
        },
        {
            "site_id": "MSH-0014",
            "site_name": "MSH-0014-Chipadze",
            "location": "Chipadze",
            "latitude": -17.3055,
            "longitude": 31.3189,
            "region": "Bindura",
            "status": "active"
        }
    ]
    
    try:
        with db.transaction() as conn:
            # Clear existing sites (if any)
            conn.execute("DELETE FROM network_sites")
            conn.execute("DELETE FROM network_cells") 
            logger.info("Cleared existing network sites and cells")
            
            # Insert Bindura cluster sites
            for i, site in enumerate(bindura_sites):
                conn.execute("""
                    INSERT INTO network_sites (
                        site_id, site_name, location, latitude, longitude,
                        region, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    site["site_id"],
                    site["site_name"],
                    site["location"],
                    site["latitude"],
                    site["longitude"],
                    site["region"],
                    site["status"],
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat()
                ))
                
                logger.info(f"Inserted site: {site['site_name']}")
                
                # Insert 6 cells for each site
                for j in range(1, 7):
                    cell_data = {
                        'cell_id': f"{site['site_id']}-{j:02d}",
                        'site_id': site['site_id'],
                        'cell_name': f"{site['site_name']} Cell {j}",
                        'technology': '4G',
                        'frequency_band': '1800MHz' if j % 2 == 1 else '900MHz',
                        'pci': (i * 6 + j) % 504,  # Physical Cell Identity
                        'sector': ((j - 1) % 3) + 1,  # Sectors 1, 2, 3
                        'azimuth': ((j - 1) % 3) * 120,  # 0, 120, 240 degrees
                        'status': 'active'
                    }
                    
                    conn.execute("""
                        INSERT INTO network_cells (
                            cell_id, site_id, cell_name, technology, frequency_band,
                            pci, sector, azimuth, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cell_data['cell_id'],
                        cell_data['site_id'], 
                        cell_data['cell_name'],
                        cell_data['technology'],
                        cell_data['frequency_band'],
                        cell_data['pci'],
                        cell_data['sector'],
                        cell_data['azimuth'],
                        cell_data['status']
                    ))
            
            logger.info(f"Successfully initialized {len(bindura_sites)} Bindura cluster sites with {len(bindura_sites) * 6} cells")
            
    except Exception as e:
        logger.error(f"Failed to initialize Bindura sites: {e}")
        raise

def update_agentic_database_fallback():
    """Update the UI database integration to use real Bindura sites"""
    
    bindura_fallback = {
        "MSH-0013-Bindura-Zaoga": {
            "site_id": "MSH-0013",
            "location": "Bindura-Zaoga",
            "status": "active",
            "cell_count": 6,
            "last_updated": datetime.now().isoformat()
        },
        "MSH-0331-Chiwaridzo 2": {
            "site_id": "MSH-0331", 
            "location": "Chiwaridzo 2",
            "status": "active",
            "cell_count": 6,
            "last_updated": datetime.now().isoformat()
        },
        "MSH-0112-Bindura Hospital": {
            "site_id": "MSH-0112",
            "location": "Bindura Hospital",
            "status": "active",
            "cell_count": 6,
            "last_updated": datetime.now().isoformat()
        },
        "MSH-0014-Chipadze": {
            "site_id": "MSH-0014",
            "location": "Chipadze", 
            "status": "active",
            "cell_count": 6,
            "last_updated": datetime.now().isoformat()
        }
    }
    
    return bindura_fallback

if __name__ == "__main__":
    initialize_bindura_sites()