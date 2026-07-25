(function () {
  const STORAGE_KEY = 'subsense-analysis';

  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  function buildMockAnalysisResult(fileName = 'financial-export.csv') {
    const normalizedName = (fileName || '').toLowerCase();
    const hasStatement = normalizedName.includes('statement');
    const hasCsv = normalizedName.includes('csv');

    const healthScore = Math.min(96, 82 + (hasStatement ? 1 : 0) + (hasCsv ? 2 : 0));
    const monthlySpend = 1840 + (hasStatement ? 140 : 0) + (hasCsv ? 90 : 0);
    const yearlySpend = monthlySpend * 12;
    const potentialSavings = 1240 + (hasStatement ? 80 : 0);

    return {
      fileName: fileName || 'financial-export.csv',
      healthScore,
      monthlySpend,
      yearlySpend,
      potentialSavings,
      spendingTrend: [68, 82, 74, 91, 96, 100],
      subscriptions: [
        { name: 'Netflix', amount: 22, cadence: 'Monthly' },
        { name: 'Spotify', amount: 16, cadence: 'Monthly' },
        { name: 'Adobe Creative Cloud', amount: 60, cadence: 'Monthly' }
      ],
      recommendations: [
        { title: 'Cancel duplicate streaming plan', amount: 180, unit: 'year', detail: 'Overlapping entertainment services' },
        { title: 'Downgrade software bundle', amount: 240, unit: 'year', detail: 'Lower tier may cover your actual usage' }
      ],
      duplicates: [
        { title: 'Prime Video + Disney+', amount: 18, unit: 'mo', detail: 'Overlap in streaming usage' },
        { title: 'Cloud Storage Duo', amount: 12, unit: 'mo', detail: 'Two plans serving the same purpose' }
      ],
      priceHikes: [
        { title: 'Phone Plan', amount: 8, unit: 'mo', detail: 'Recent renewal increase' },
        { title: 'Insurance Bundle', amount: 14, unit: 'mo', detail: 'Price adjustment detected' }
      ],
      completedAt: new Date().toISOString()
    };
  }

  function saveAnalysisResult(result) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(result));
      return true;
    } catch (error) {
      console.warn('SubSense AI could not save analysis result:', error);
      return false;
    }
  }

  function getStoredAnalysis() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (error) {
      console.warn('SubSense AI could not read analysis result:', error);
      return null;
    }
  }

  function clearStoredAnalysis() {
    try {
      localStorage.removeItem(STORAGE_KEY);
      return true;
    } catch (error) {
      console.warn('SubSense AI could not clear analysis result:', error);
      return false;
    }
  }

  async function analyzeFinancialData(file) {
    const fileName = file?.name || 'financial-export.csv';
    await delay(1200);
    const result = buildMockAnalysisResult(fileName);
    saveAnalysisResult(result);
    return result;
  }

  function formatCurrency(value) {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
      currencyDisplay: 'narrowSymbol'
    }).format(value);
  }

  function formatPercent(value) {
    return `${value}%`;
  }

  window.SubSenseAPI = {
    STORAGE_KEY,
    analyzeFinancialData,
    saveAnalysisResult,
    getStoredAnalysis,
    clearStoredAnalysis,
    formatCurrency,
    formatPercent
  };
})();
