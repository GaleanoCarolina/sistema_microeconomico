from database.connection import backup_database, restore_database
class BackupService:
    def create(self, target=None): return backup_database(target)
    def restore(self, source): return restore_database(source)
