import json
import logging
import os
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path

from config import CLOUD_STORAGE, BACKUP_SYNC_INTERVAL

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('backup_sync')

class BackupSyncManager:
    def __init__(self):
        """Initialize the backup sync manager"""
        self.cloud_storage = CLOUD_STORAGE
        
        # Initialize cloud storage directories
        for provider, directory in self.cloud_storage.items():
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Initialized cloud storage directory for {provider}: {directory}")
    
    def _copy_file(self, source_file, target_dir):
        """Copy a file from source to target directory"""
        try:
            # Create target directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy the file
            target_file = os.path.join(target_dir, os.path.basename(source_file))
            shutil.copy2(source_file, target_file)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to copy file {source_file} to {target_dir}: {str(e)}")
            return False
    
    def sync_across_providers(self):
        """Sync files across all cloud providers"""
        try:
            providers = list(self.cloud_storage.keys())
            files_synced = 0
            total_files = 0
            
            # Log the sync start
            logger.info("Starting sync across all cloud providers")
            
            # For each provider, sync its files to all other providers
            for source_provider in providers:
                source_dir = self.cloud_storage[source_provider]
                
                # Skip if source directory doesn't exist
                if not os.path.exists(source_dir):
                    logger.warning(f"Source directory for {source_provider} doesn't exist: {source_dir}")
                    continue
                
                # Get all files in the source directory
                source_files = []
                for root, _, files in os.walk(source_dir):
                    for file in files:
                        # Skip hidden files and directories
                        if not file.startswith('.'):
                            source_files.append(os.path.join(root, file))
                
                total_files += len(source_files)
                
                # For each file in source provider, copy to all other providers
                for source_file in source_files:
                    # Determine the relative path from the source directory
                    rel_path = os.path.relpath(source_file, source_dir)
                    
                    # For each target provider, copy the file
                    for target_provider in providers:
                        if target_provider != source_provider:
                            target_dir = os.path.join(self.cloud_storage[target_provider], os.path.dirname(rel_path))
                            
                            # Create the target directory if it doesn't exist
                            os.makedirs(target_dir, exist_ok=True)
                            
                            # Copy the file
                            target_file = os.path.join(target_dir, os.path.basename(source_file))
                            
                            # Only copy if the file doesn't exist or is newer
                            if (not os.path.exists(target_file) or 
                                os.path.getmtime(source_file) > os.path.getmtime(target_file)):
                                self._copy_file(source_file, target_dir)
                                files_synced += 1
            
            # Log sync completion
            logger.info(f"Sync completed. {files_synced} files synced out of {total_files} total files.")
            
            # Create a marker file with the sync timestamp
            for provider, directory in self.cloud_storage.items():
                marker_file = os.path.join(directory, ".sync_marker")
                try:
                    with open(marker_file, 'w') as f:
                        json.dump({
                            'last_sync': datetime.now().isoformat(),
                            'files_synced': files_synced,
                            'total_files': total_files
                        }, f)
                except Exception as e:
                    logger.error(f"Failed to create sync marker file for {provider}: {str(e)}")
            
            return files_synced, total_files
        
        except Exception as e:
            logger.error(f"Error in sync_across_providers: {str(e)}")
            return 0, 0
    
    def run_backup_sync_thread(self):
        """Run backup sync in a loop at specified intervals"""
        while True:
            try:
                files_synced, total_files = self.sync_across_providers()
                logger.info(f"Backup sync completed. Synced {files_synced} of {total_files} files. Next sync in {BACKUP_SYNC_INTERVAL} seconds.")
                time.sleep(BACKUP_SYNC_INTERVAL)
            except Exception as e:
                logger.error(f"Error in backup sync thread: {str(e)}")
                time.sleep(60)  # Wait a minute and try again
    
    def start_backup_sync(self):
        """Start backup sync in a background thread"""
        sync_thread = threading.Thread(target=self.run_backup_sync_thread, daemon=True)
        sync_thread.start()
        logger.info(f"Backup sync started in background thread (interval: {BACKUP_SYNC_INTERVAL}s)")
        return sync_thread
    
    def get_sync_status(self):
        """Get the sync status for all providers"""
        status = {}
        
        for provider, directory in self.cloud_storage.items():
            marker_file = os.path.join(directory, ".sync_marker")
            
            if os.path.exists(marker_file):
                try:
                    with open(marker_file, 'r') as f:
                        status[provider] = json.load(f)
                except Exception as e:
                    logger.error(f"Failed to read sync marker file for {provider}: {str(e)}")
                    status[provider] = {
                        'last_sync': None,
                        'files_synced': 0,
                        'total_files': 0,
                        'error': str(e)
                    }
            else:
                status[provider] = {
                    'last_sync': None,
                    'files_synced': 0,
                    'total_files': 0
                }
        
        return status
    
    def get_file_counts(self):
        """Get the file count for each provider"""
        counts = {}
        
        for provider, directory in self.cloud_storage.items():
            if not os.path.exists(directory):
                counts[provider] = 0
                continue
            
            # Count files in the directory (exclude hidden files)
            file_count = 0
            for _, _, files in os.walk(directory):
                file_count += sum(1 for f in files if not f.startswith('.'))
            
            counts[provider] = file_count
        
        return counts

if __name__ == "__main__":
    # When run directly, start backup sync
    sync_manager = BackupSyncManager()
    sync_manager.start_backup_sync()
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Backup sync stopped")
