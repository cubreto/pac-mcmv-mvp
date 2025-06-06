-- 004_sync_mcmv_table.sql
-- Resets `projeto_status` to the Mac-validated dataset (1 498 MCMV rows)

TRUNCATE projeto_status;

-- If you want to embed the data directly, you could paste the INSERTs
-- from projeto_status_mac.sql here, but that file is ~10 MB.  Instead,
-- keep the dump outside the repo and re-run the Mac→EC2 copy when needed.

