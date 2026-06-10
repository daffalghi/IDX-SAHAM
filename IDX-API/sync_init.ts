import * as sync from '@app/Backend/Sync/index.ts';

async function main() {
  // Use yesterday's date (assuming today is 2026-06-10, yesterday was 2026-06-09)
  const dateStr = '20260609';
  const year = 2026;
  const month = 6;

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
