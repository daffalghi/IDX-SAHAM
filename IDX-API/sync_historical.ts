import * as sync from '@app/Backend/Sync/index.ts';

async function main() {
  // Syncing for the past 5 days (June 4th to June 8th, 2026)
  const dates = ['20260608', '20260605', '20260604', '20260603', '20260602']; // Skipping weekend
  
  for (const dateStr of dates) {
    try {
      console.log(`\n--- Syncing Data for ${dateStr} ---`);
      
      try {
        console.log('Syncing Stock Summary...');
        await sync.syncStockSummary(dateStr);
      } catch(e) {
        console.error('Failed Stock Summary', e);
      }
      
      try {
        console.log('Syncing Broker Summary...');
        await sync.syncBrokerSummary(dateStr);
      } catch(e) {
        console.error('Failed Broker Summary', e);
      }
      
      // Delay slightly between requests to be polite to the IDX API
      await new Promise(r => setTimeout(r, 2000));
      
    } catch (e) {
      console.error(`Error on date ${dateStr}:`, e);
    }
  }
  
  console.log('\nHistorical sync completed!');
}

main().catch(console.error);
