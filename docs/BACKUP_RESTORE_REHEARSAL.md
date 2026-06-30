# PostgreSQL backup and restore rehearsal

Use a separate test database for restore rehearsals. Never rehearse against the live AI Studio database.

## Backup with pgAdmin

1. Right-click `ai_studio_db`.
2. Choose **Backup**.
3. Select **Custom** format.
4. Save the backup outside the project directory.
5. Record the date and file size.

## Backup with PowerShell

Open a PowerShell session where `DATABASE_URL` is set, then run:

```powershell
.\scripts\backup-postgres.ps1
```

The script uses `pg_dump` and creates a timestamped custom-format backup.

## Restore rehearsal

1. Create a separate empty PostgreSQL database, for example `ai_studio_restore_test`.
2. Build a connection URL for that test database.
3. Run:

```powershell
.\scripts\restore-rehearsal.ps1 `
  -BackupFile "C:\path\to\ai-studio-YYYYMMDD-HHMMSS.dump" `
  -TargetDatabaseUrl "postgresql://USER:PASSWORD@localhost:5432/ai_studio_restore_test"
```

4. Point a temporary AI Studio `.env` at the test database.
5. Run `python -m flask --app app:create_app db current`.
6. Confirm the expected migration head.
7. Sign in and verify chats, messages, documents, website sources, and account data.
8. Delete the rehearsal database after verification.

Do not paste production credentials into documentation, screenshots, Git, or chat messages.
