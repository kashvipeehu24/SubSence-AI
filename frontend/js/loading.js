document.addEventListener('DOMContentLoaded', () => {
  const steps = [
    'Scanning Transactions...',
    'Finding Recurring Payments...',
    'Detecting Hidden Subscriptions...',
    'Analyzing Financial Leaks...',
    'Calculating Financial Health...',
    'Generating AI Recommendations...',
    'Preparing Dashboard...'
  ];

  const progressBar = document.getElementById('progressBar');
  const loadingStep = document.getElementById('loadingStep');
  const loadingMessage = document.getElementById('loadingMessage');

  if (!progressBar || !loadingStep || !loadingMessage) return;

  let progress = 0;
  const interval = setInterval(() => {
    progress += 14;
    if (progress > 100) progress = 100;
    progressBar.style.width = progress + '%';

    const index = Math.min(Math.floor(progress / 14), steps.length - 1);
    loadingStep.textContent = steps[index];

    if (progress === 100) {
      clearInterval(interval);
      loadingMessage.textContent = 'Analysis complete. Redirecting...';
      setTimeout(() => {
        window.location.href = 'dashboard.html';
      }, 700);
    }
  }, 500);
});
