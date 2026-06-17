import * as sync from '@app/Backend/Sync/index.ts';

async function main() {
  const now = new Date();
  // Jika jam < 16:00 WIB (09:00 UTC), ambil tanggal kemarin karena bursa hari ini belum tutup
  if (now.getUTCHours() < 9) {
    now.setDate(now.getDate() - 1);
  }
  
  // Skip weekend (Minggu = 0, Sabtu = 6), ambil hari Jumat
  if (now.getDay() === 0) now.setDate(now.getDate() - 2);
  if (now.getDay() === 6) now.setDate(now.getDate() - 1);
  
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  
  const dateStr = `${y}${m}${d}`;
  const year = y;
  const month = now.getMonth() + 1;

  try {
    console.log('Syncing Stock Summary for ' + dateStr);
    await sync.syncStockSummary(dateStr);
  } catch (e) {
    console.error('Error syncing Stock Summary:', e);
  }

  try {
    console.log('Syncing Foreign Trading for ' + year + '-' + month);
    await sync.syncForeignTrading(year, month);
  } catch (e) {
    console.error('Error syncing Foreign Trading:', e);
  }

  try {
    console.log('Syncing Broker Summary for ' + dateStr);
    await sync.syncBrokerSummary(dateStr);
  } catch (e) {
    console.error('Error syncing Broker Summary:', e);
  }

  console.log('Initial sync done.');
}

main().catch(console.error);
