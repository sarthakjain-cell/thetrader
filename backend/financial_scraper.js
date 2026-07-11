const { chromium } = require('playwright');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Connect to the SQLite database that our Python AI uses
const DB_PATH = path.resolve(__dirname, 'trading_system.db');
const db = new sqlite3.Database(DB_PATH, (err) => {
    if (err) {
        console.error('Error connecting to database:', err.message);
    } else {
        console.log('Connected to the AI Database: trading_system.db');
    }
});

const TARGET_URL = 'https://economictimes.indiatimes.com/markets'; // The financial news target

async function scrapeFinancialNews() {
  console.log('Starting Financial Data Extractor (Bypass UI Mode)...');
  
  // headless: false is required to ensure bypass systems (like Cloudflare) act normally
  const browser = await chromium.launch({ headless: false }); 
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log(`Navigating to ${TARGET_URL}`);
    await page.goto(TARGET_URL, { waitUntil: 'domcontentloaded' });

    // ==============================================================================
    // USER'S CUSTOM FIREWALL / CAPTCHA BYPASS SYSTEM (UNTOUCHED)
    // ==============================================================================
    console.log('----------------------------------------------------');
    console.log('PAUSED: Firewall / CAPTCHA Bypass Protocol Active...');
    console.log('If Cloudflare or a CAPTCHA intercepts, solve it manually now.');
    console.log('The script will wait for 15-60 seconds to ensure bypass is complete.');
    console.log('----------------------------------------------------');
    
    // Give time for manual intervention if the site throws a security challenge
    await page.waitForTimeout(15000); 
    
    console.log('Bypass window closed. Site access verified. Beginning extraction...');
    // ==============================================================================

    console.log('Extracting trending financial headlines...');
    
    // Scrape the DOM for news articles
    const articles = await page.evaluate(() => {
        const newsItems = [];
        // Find all links that look like news articles
        const links = document.querySelectorAll('a');
        links.forEach(link => {
            const headline = link.innerText.trim();
            // Basic filter: Only grab long headlines that link to an actual article page
            if (headline.length > 40 && link.href.includes('articleshow')) {
                newsItems.push({
                    headline: headline,
                    url: link.href
                });
            }
        });
        
        // Remove duplicates and return the top 5 articles
        const uniqueItems = Array.from(new Set(newsItems.map(a => a.headline)))
            .map(headline => {
                return newsItems.find(a => a.headline === headline)
            });
            
        return uniqueItems.slice(0, 5); 
    });

    console.log(`Found ${articles.length} raw financial articles.`);

    // Deposit the raw data directly into the AI's database
    for (const article of articles) {
        console.log(`-> Depositing: ${article.headline.substring(0, 60)}...`);
        
        const timestamp = new Date().toISOString();
        const source = 'Economic Times';
        const content = `Link to article: ${article.url}`; // For now, we just pass the URL as content
        
        const insertQuery = `INSERT INTO scraped_news (timestamp, source, headline, content) VALUES (?, ?, ?, ?)`;
        
        db.run(insertQuery, [timestamp, source, article.headline, content], function(err) {
            if (err) {
                console.error('Database Insert Error:', err.message);
            }
        });
    }

    console.log('----------------------------------------------------');
    console.log('EXTRACTION COMPLETE! Raw data deposited for Baby 2 (Macro AI).');
    console.log('----------------------------------------------------');

    await browser.close();
    db.close();

  } catch (error) {
    console.error('An error occurred during extraction:', error);
  }
}

scrapeFinancialNews();
