document.addEventListener('DOMContentLoaded', () => {
  const statCards = document.querySelectorAll('.stat-card');
  const dashboardCards = document.querySelectorAll('.dashboard-card');
  const itemRows = document.querySelectorAll('.item-row');
  const dashboardStatus = document.getElementById('dashboardStatus');
  const healthSummary = document.getElementById('healthSummary');

  const revealElements = (elements, delay = 80) => {
    elements.forEach((element, index) => {
      element.style.opacity = '0';
      element.style.transform = 'translateY(18px)';

      setTimeout(() => {
        element.style.transition = 'all 0.45s ease';
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
      }, delay * index);
    });
  };

  const animateStatHeadings = () => {
    document.querySelectorAll('.stat-card h3').forEach((heading) => {
      const rawText = heading.textContent.trim();
      const numericValue = Number(rawText.replace(/[₹,+/%]/g, '').replace(/,/g, ''));

      if (!Number.isFinite(numericValue)) return;

      const prefix = rawText.includes('₹') ? '₹' : '';
      const suffix = rawText.includes('%') ? '%' : '';
      const duration = 800;
      const stepTime = 24;
      const steps = Math.max(1, Math.round(duration / stepTime));
      const increment = numericValue / steps;
      let currentStep = 0;

      heading.textContent = `${prefix}0${suffix}`;

      const timer = setInterval(() => {
        currentStep += 1;
        const value = Math.min(Math.round(currentStep * increment), numericValue);
        heading.textContent = `${prefix}${value.toLocaleString('en-IN')}${suffix}`;

        if (currentStep >= steps) {
          clearInterval(timer);
        }
      }, stepTime);
    });
  };

  const animateHealthRing = () => {
    const healthRing = document.querySelector('.health-ring');
    if (healthRing) {
      const targetScore = Number((healthRing.textContent || '0').replace(/%/g, '')) || 0;
      let currentScore = 0;

      const animateRing = setInterval(() => {
        currentScore += 1;
        healthRing.textContent = `${currentScore}%`;
        healthRing.style.background = `conic-gradient(var(--accent-2) ${currentScore}%, #23374b 0)`;

        if (currentScore >= targetScore) {
          clearInterval(animateRing);
          healthRing.textContent = `${targetScore}%`;
        }
      }, 18);
    }
  };

  const attachHoverEffects = () => {
    document.querySelectorAll('.stat-card, .dashboard-card, .item-row').forEach((card) => {
      card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-4px)';
        card.style.borderColor = '#63e4c0';
      });

      card.addEventListener('mouseleave', () => {
        card.style.transform = '';
        card.style.borderColor = '';
      });
    });
  };

  const updateStatus = (message) => {
    if (dashboardStatus) {
      dashboardStatus.textContent = message;
    }
  };

  const buildEmptyState = (message) => `<div class="empty-state">${message}</div>`;

  const formatCurrency = (value) => new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
    currencyDisplay: 'narrowSymbol'
  }).format(value);

  const renderDashboard = (dashboardData, aiData) => {
    const health = dashboardData?.financial_health || {};
    const cards = dashboardData?.cards || {};
    const subscriptions = dashboardData?.subscriptions || [];
    const recommendations = dashboardData?.recommendations || [];
    const duplicates = dashboardData?.duplicate_subscriptions || [];
    const priceHikes = dashboardData?.price_hikes || [];

    const statHeadings = document.querySelectorAll('.stat-card h3');
    if (statHeadings[0]) statHeadings[0].textContent = `${health.score ?? 0}%`;
    if (statHeadings[1]) statHeadings[1].textContent = formatCurrency(cards.monthly_spending || 0);
    if (statHeadings[2]) statHeadings[2].textContent = formatCurrency(cards.yearly_spending || 0);
    if (statHeadings[3]) statHeadings[3].textContent = formatCurrency(cards.monthly_savings || 0);

    const healthRing = document.querySelector('.health-ring');
    if (healthRing) {
      healthRing.textContent = `${health.score ?? 0}%`;
      healthRing.style.background = `conic-gradient(var(--accent-2) ${health.score ?? 0}%, #23374b 0)`;
    }

    if (healthSummary) {
      healthSummary.textContent = aiData?.financial_summary?.summary || aiData?.summary || 'AI analysis is available for review.';
    }

    const subscriptionsCard = Array.from(document.querySelectorAll('.dashboard-card')).find((card) =>
      card.querySelector('h5')?.textContent.includes('Subscriptions')
    );
    if (subscriptionsCard) {
      subscriptionsCard.innerHTML = `
        <h5 class="fw-semibold mb-3">Subscriptions</h5>
        ${subscriptions.length ? subscriptions.map((item) => `
          <div class="item-row">
            <div class="d-flex justify-content-between align-items-start"><strong>${item.merchant || 'Subscription'}</strong><span class="value">${formatCurrency(item.monthly_cost || 0)}</span></div>
            <div class="text-muted small">${item.billing_cycle || 'Monthly'}</div>
          </div>
        `).join('') : buildEmptyState('No recurring subscriptions were detected.')}
      `;
    }

    const recommendationsCard = Array.from(document.querySelectorAll('.dashboard-card')).find((card) =>
      card.querySelector('h5')?.textContent.includes('Savings Recommendations')
    );
    if (recommendationsCard) {
      recommendationsCard.innerHTML = `
        <h5 class="fw-semibold mb-3">Savings Recommendations</h5>
        ${recommendations.length ? recommendations.map((item) => `
          <div class="item-row">
            <div class="d-flex justify-content-between align-items-start"><strong>${item}</strong><span class="value text-success">Action</span></div>
            <div class="text-muted small">AI recommendation from the backend</div>
          </div>
        `).join('') : buildEmptyState('No recommendations were generated yet.')}
      `;
    }

    const duplicatesCard = Array.from(document.querySelectorAll('.dashboard-card')).find((card) =>
      card.querySelector('h5')?.textContent.includes('Duplicate Subscriptions')
    );
    if (duplicatesCard) {
      duplicatesCard.innerHTML = `
        <h5 class="fw-semibold mb-3">Duplicate Subscriptions</h5>
        ${duplicates.length ? duplicates.map((item) => `
          <div class="item-row">
            <div class="d-flex justify-content-between align-items-start"><strong>${(item.services || []).join(', ')}</strong><span class="value">${formatCurrency(item.monthly_cost || 0)}/month</span></div>
            <div class="text-muted small">${item.category || 'Duplicate service'}</div>
          </div>
        `).join('') : buildEmptyState('No duplicate subscriptions were found.')}
      `;
    }

    const priceHikesCard = Array.from(document.querySelectorAll('.dashboard-card')).find((card) =>
      card.querySelector('h5')?.textContent.includes('Price Hikes')
    );
    if (priceHikesCard) {
      priceHikesCard.innerHTML = `
        <h5 class="fw-semibold mb-3">Price Hikes</h5>
        ${priceHikes.length ? priceHikes.map((item) => `
          <div class="item-row">
            <div class="d-flex justify-content-between align-items-start"><strong>${item.merchant || 'Merchant'}</strong><span class="value">+${formatCurrency(item.increase || 0)}/month</span></div>
            <div class="text-muted small">${item.percentage ? `${item.percentage}% increase` : 'Price increase detected'}</div>
          </div>
        `).join('') : buildEmptyState('No price increases were detected.')}
      `;
    }

    const updatedDashboardCards = document.querySelectorAll('.dashboard-card');
    const updatedItemRows = document.querySelectorAll('.item-row');
    revealElements(updatedDashboardCards, 100);
    revealElements(updatedItemRows, 60);
    animateStatHeadings();
    animateHealthRing();
    attachHoverEffects();
  };

  const loadDashboardData = async () => {
    try {
      updateStatus('Loading your latest analysis…');
      const [dashboardResponse, aiResponse] = await Promise.all([
        fetch('/api/dashboard'),
        fetch('/api/ai')
      ]);

      if (!dashboardResponse.ok || !aiResponse.ok) {
        throw new Error('Unable to load dashboard data');
      }

      const dashboardData = await dashboardResponse.json();
      const aiData = await aiResponse.json();
      renderDashboard(dashboardData, aiData);
      updateStatus('Analysis loaded from the live backend.');
    } catch (error) {
      console.error('Dashboard load failed', error);
      const healthRing = document.querySelector('.health-ring');
      if (healthRing) {
        healthRing.textContent = '—';
      }
      if (healthSummary) {
        healthSummary.textContent = 'Backend data is unavailable right now.';
      }
      updateStatus('Unable to load the latest analysis right now.');
    }
  };

  revealElements(statCards, 90);
  revealElements(dashboardCards, 100);
  revealElements(itemRows, 60);
  attachHoverEffects();
  animateStatHeadings();
  animateHealthRing();

  const downloadButton = document.querySelector('.navbar .btn-primary');
  if (downloadButton) {
    downloadButton.addEventListener('click', (event) => {
      event.preventDefault();
      const note = document.createElement('div');
      note.textContent = 'Report prepared for download';
      note.style.position = 'fixed';
      note.style.right = '20px';
      note.style.bottom = '20px';
      note.style.background = '#111c2f';
      note.style.color = '#f8fafc';
      note.style.padding = '0.8rem 1rem';
      note.style.borderRadius = '999px';
      note.style.border = '1px solid #63e4c0';
      note.style.zIndex = '1000';
      document.body.appendChild(note);

      setTimeout(() => {
        note.remove();
      }, 1800);
    });
  }

  loadDashboardData();
});
