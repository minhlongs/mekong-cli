/**
 * ═══════════════════════════════════════════════
 *  F&B CAFFE CONTAINER — Loyalty UI Renderer
 *  UI Components for Loyalty System
 * ═══════════════════════════════════════════════
 */

import {
  initLoyaltySystem,
  getCurrentTier,
  getNextTier,
  getTierProgress,
  getAvailableRewards,
  getTransactionHistory,
  getRedemptionHistory,
  getUserLoyaltySummary,
  redeemReward,
  generateReferralCode,
  addReferral
} from './loyalty.js';

// ─── DOM Elements ───
const ui = {
  loyaltyCard: null,
  tierBadgesRow: null,
  tierProgressFill: null,
  tierProgressPoints: null,
  tierProgressHint: null,
  pointsNeeded: null,
  tierBenefits: null,
  rewardsGrid: null,
  rewardsFilter: null,
  transactionsList: null,
  redemptionsList: null,
  referralCode: null,
  copyReferralBtn: null,
  referralCodeHero: null,
  copyReferralBtnHero: null,
  shareZalo: null,
  shareFacebook: null,
  shareCopy: null,
  redemptionModal: null,
  redemptionModalBody: null,
  modalClose: null,
  toastContainer: null,
  historyTabs: null,
  // New gamification elements
  achievementsGrid: null,
  pointsTimeline: null,
  currentTierIcon: null,
  currentTierName: null,
  nextTierName: null,
  nextTierPoints: null,
  tierProgressPercent: null
};

// ─── Initialize ───
document.addEventListener('DOMContentLoaded', async () => {
  cacheElements();
  await initLoyaltyUI();
  setupEventListeners();
  initThemeToggle();
});

// ─── Cache DOM Elements ───
function cacheElements() {
  ui.loyaltyCard = document.getElementById('loyaltyCard');
  ui.tierBadgesRow = document.getElementById('tierBadgesRow');
  ui.tierProgressFill = document.getElementById('tierProgressFill');
  ui.tierProgressPoints = document.getElementById('tierProgressPoints');
  ui.tierProgressHint = document.getElementById('tierProgressHint');
  ui.pointsNeeded = document.getElementById('pointsNeeded');
  ui.tierBenefits = document.getElementById('tierBenefits');
  ui.rewardsGrid = document.getElementById('rewardsGrid');
  ui.rewardsFilter = document.getElementById('rewardsFilter');
  ui.transactionsList = document.getElementById('transactionsList');
  ui.themeToggle = document.getElementById('themeToggle');
  ui.redemptionsList = document.getElementById('redemptionsList');
  ui.referralCode = document.getElementById('referralCode');
  ui.copyReferralBtn = document.getElementById('copyReferralBtn');
  ui.referralCodeHero = document.getElementById('referralCodeHero');
  ui.copyReferralBtnHero = document.getElementById('copyReferralBtnHero');
  ui.shareZalo = document.getElementById('shareZalo');
  ui.shareFacebook = document.getElementById('shareFacebook');
  ui.shareCopy = document.getElementById('shareCopy');
  ui.redemptionModal = document.getElementById('redemptionModal');
  ui.redemptionModalBody = document.getElementById('redemptionModalBody');
  ui.modalClose = document.getElementById('modalClose');
  ui.toastContainer = document.getElementById('toastContainer');
  ui.historyTabs = document.querySelectorAll('.history-tab');
  // New gamification elements
  ui.achievementsGrid = document.getElementById('achievementsGrid');
  ui.pointsTimeline = document.getElementById('pointsTimeline');
  ui.currentTierIcon = document.getElementById('currentTierIcon');
  ui.currentTierName = document.getElementById('currentTierName');
  ui.nextTierName = document.getElementById('nextTierName');
  ui.nextTierPoints = document.getElementById('nextTierPoints');
  ui.tierProgressPercent = document.getElementById('tierProgressPercent');
}

// ─── Initialize Loyalty UI ───
async function initLoyaltyUI() {
  try {
    const { config, user } = await initLoyaltySystem();

    // Render all components
    renderLoyaltyCard();
    renderTierBadges();
    renderTierProgress();
    renderTierBenefits();
    renderAchievements();
    renderPointsTimeline();
    renderRewards('all');
    renderTransactions();
    renderRedemptions();
    renderReferralCode();

    // Listen for tier upgrade events
    window.addEventListener('loyalty-tier-upgrade', handleTierUpgrade);

    showToast('🎉 Chào mừng đến F&B Loyalty Club!', 'success');
  } catch (error) {
    showToast('⚠️ Không thể tải chương trình loyalty', 'error');
  }
}

// ─── Render Loyalty Card ───
function renderLoyaltyCard() {
  const summary = getUserLoyaltySummary();
  const tier = summary.tier;

  ui.loyaltyCard.innerHTML = `
        <div class="loyalty-card-header">
            <div class="member-info">
                <span class="member-label">Thành Viên</span>
                <code class="member-id">${summary.memberId}</code>
            </div>
            <div class="tier-badge-large" style="background: ${tier.gradient}">
                <span class="tier-icon">${tier.icon}</span>
                <span class="tier-name">${tier.name}</span>
            </div>
        </div>

        <div class="loyalty-card-body">
            <div class="points-display">
                <span class="points-value">${formatNumber(summary.availablePoints)}</span>
                <span class="points-label">points available</span>
            </div>

            <div class="points-breakdown">
                <div class="breakdown-item">
                    <span class="breakdown-label">Lifetime</span>
                    <span class="breakdown-value">${formatNumber(summary.lifetimePoints)}</span>
                </div>
                <div class="breakdown-item">
                    <span class="breakdown-label">Rewards</span>
                    <span class="breakdown-value">${summary.activeRewards}/${summary.totalRewards}</span>
                </div>
            </div>
        </div>

        <div class="loyalty-card-footer">
            <span class="card-decoration">F&B LOYALTY CLUB</span>
        </div>
    `;

  // Add animation
  ui.loyaltyCard.classList.add('card-enter');
}

// ─── Render Tier Badges Row ───
function renderTierBadges() {
  const currentTier = getCurrentTier();
  const tiers = window.LoyaltySystem?.config?.tiers || [];

  ui.tierBadgesRow.innerHTML = tiers.map((tier, index) => {
    const isCurrentTier = tier.id === currentTier.id;
    const isUnlocked = tier.minPoints <= currentTier.minPoints;
    const iconStyle = isUnlocked ? '' : 'filter:grayscale(1);opacity:0.4;';

    return `
            <div class="tier-badge-item ${isCurrentTier ? 'active' : ''} ${isUnlocked ? 'unlocked' : 'locked'}">
                <div class="tier-badge-icon" style="${iconStyle}">
                    ${tier.icon}
                </div>
                <span class="tier-badge-name">${tier.name}</span>
                <span class="tier-badge-points">${tier.minPoints.toLocaleString('vi-VN')} pts</span>
                ${index < tiers.length - 1 ? '<div class="tier-connector"></div>' : ''}
            </div>
        `;
  }).join('');
}

// ─── Render Tier Progress ───
function renderTierProgress() {
  const progress = getTierProgress();
  const currentTier = getCurrentTier();
  const nextTier = getNextTier();

  ui.tierProgressFill.style.width = `${progress.percent}%`;
  ui.tierProgressPoints.textContent = `${formatNumber(progress.current)} / ${progress.isMaxTier ? '∞' : formatNumber(progress.current + progress.needed)}`;

  // Update percentage
  ui.tierProgressPercent.textContent = `${Math.round(progress.percent)}%`;

  // Update tier icons and names
  ui.currentTierIcon.textContent = currentTier.icon;
  ui.currentTierName.textContent = currentTier.name;

  if (nextTier) {
    ui.nextTierName.textContent = nextTier.name;
    ui.nextTierPoints.textContent = `${formatNumber(nextTier.minPoints)} pts`;
  } else {
    ui.nextTierName.textContent = 'Max Tier';
    ui.nextTierPoints.textContent = '✓';
  }

  // Update progress bar color based on tier
  const progressBar = ui.tierProgressFill;
  progressBar.className = 'progress-indicator';
  if (currentTier.id === 'dong') {
    progressBar.classList.add('tier-bronze');
  } else if (currentTier.id === 'bac') {
    progressBar.classList.add('tier-silver');
  } else if (currentTier.id === 'vang') {
    progressBar.classList.add('tier-gold');
  } else if (currentTier.id === 'kim-cuong') {
    progressBar.classList.add('tier-diamond');
  }

  if (progress.isMaxTier) {
    ui.tierProgressHint.innerHTML = '🏆 Bạn đã đạt hạng cao nhất!';
    ui.tierProgressHint.className = 'm3-progress-hint max-tier';
  } else {
    ui.tierProgressHint.innerHTML = `
            Còn <strong id="pointsNeeded">${formatNumber(progress.needed)}</strong> điểm để lên
            <strong>${progress.nextTierName}</strong>
        `;
  }
}

// ─── Render Tier Benefits ───
function renderTierBenefits() {
  const currentTier = getCurrentTier();

  ui.tierBenefits.innerHTML = `
        <div class="benefits-header">
            <h3>🎁 Đặc Quyền Hạng ${currentTier.name}</h3>
        </div>
        <div class="benefits-grid">
            ${currentTier.benefits.map(benefit => `
                <div class="benefit-item">
                    <span class="benefit-check">✓</span>
                    <span class="benefit-text">${benefit}</span>
                </div>
            `).join('')}
        </div>
    `;
}

// ─── Render Achievement Badges ───
function renderAchievements() {
  const summary = getUserLoyaltySummary();
  const transactions = getTransactionHistory(100);

  // Define all possible achievements
  const achievements = [
    {
      id: 'first_order',
      name: 'Đơn Đầu Tiên',
      description: 'Hoàn thành đơn hàng đầu tiên',
      icon: '🎯',
      variant: 'first-order',
      unlocked: transactions.some(t => t.source === 'purchase' || t.type === 'earn'),
      progress: null
    },
    {
      id: 'order_10',
      name: 'Khách Quen',
      description: 'Hoàn thành 10 đơn hàng',
      icon: '⭐',
      variant: 'order-10',
      unlocked: transactions.filter(t => t.source === 'purchase').length >= 10,
      progress: `${transactions.filter(t => t.source === 'purchase').length}/10`
    },
    {
      id: 'order_50',
      name: 'Thượng Khách',
      description: 'Hoàn thành 50 đơn hàng',
      icon: '👑',
      variant: 'order-50',
      unlocked: transactions.filter(t => t.source === 'purchase').length >= 50,
      progress: `${transactions.filter(t => t.source === 'purchase').length}/50`
    },
    {
      id: 'birthday',
      name: 'Sinh Nhật Vui Vẻ',
      description: 'Nhận quà sinh nhật',
      icon: '🎂',
      variant: 'birthday',
      unlocked: transactions.some(t => t.source === 'birthday'),
      progress: null
    },
    {
      id: 'high_spender',
      name: 'Chi Tiêu Mạnh Tay',
      description: 'Tích lũy 10.000 điểm',
      icon: '💰',
      variant: 'high-spender',
      unlocked: summary.lifetimePoints >= 10000,
      progress: `${formatNumber(summary.lifetimePoints)}/10.000`
    },
    {
      id: 'referrer',
      name: 'Người Giới Thiệu',
      description: 'Giới thiệu 5 bạn bè',
      icon: '👥',
      variant: 'referrer',
      unlocked: transactions.filter(t => t.source === 'referral').length >= 5,
      progress: `${transactions.filter(t => t.source === 'referral').length}/5`
    },
    {
      id: 'tier_silver',
      name: 'Hạng Bạc',
      description: 'Đạt hạng thành viên Bạc',
      icon: '🥈',
      variant: 'tier-silver',
      unlocked: summary.tier.id === 'bac' || summary.tier.id === 'vang' || summary.tier.id === 'kim-cuong',
      progress: null
    },
    {
      id: 'tier_gold',
      name: 'Hạng Vàng',
      description: 'Đạt hạng thành viên Vàng',
      icon: '🥇',
      variant: 'tier-gold',
      unlocked: summary.tier.id === 'vang' || summary.tier.id === 'kim-cuong',
      progress: null
    },
    {
      id: 'tier_diamond',
      name: 'Hạng Kim Cương',
      description: 'Đạt hạng thành viên Kim Cương',
      icon: '💎',
      variant: 'tier-diamond',
      unlocked: summary.tier.id === 'kim-cuong',
      progress: null
    }
  ];

  if (ui.achievementsGrid) {
    ui.achievementsGrid.innerHTML = achievements.map(ach => `
            <div class="achievement-badge ${ach.variant} ${ach.unlocked ? 'unlocked' : 'locked'}">
                <div class="badge-icon">
                    ${ach.icon}
                </div>
                <div class="badge-name">${ach.name}</div>
                <div class="badge-description">${ach.description}</div>
                ${ach.progress ? `<div class="badge-progress">${ach.progress}</div>` : ''}
                ${!ach.unlocked ? '<div class="badge-locked-overlay">🔒</div>' : ''}
            </div>
        `).join('');
  }
}

// ─── Render Points Timeline ───
function renderPointsTimeline() {
  const transactions = getTransactionHistory(20);

  if (!ui.pointsTimeline) {return;}

  if (transactions.length === 0) {
    ui.pointsTimeline.innerHTML = `
            <div class="timeline-empty">
                <span class="empty-icon">📜</span>
                <p>Chưa có lịch sử giao dịch nào</p>
                <p class="timeline-hint">Thực hiện đơn hàng đầu tiên để bắt đầu tích điểm!</p>
            </div>
        `;
    return;
  }

  ui.pointsTimeline.innerHTML = transactions.map(txn => {
    const isPositive = txn.points > 0;
    const typeClass = txn.source === 'birthday' ? 'bonus' :
      txn.source === 'tier_upgrade' ? 'tier-upgrade' :
        isPositive ? 'earned' : 'spent';
    const icon = getTransactionIcon(txn.source || txn.type);

    return `
            <div class="timeline-item ${typeClass}">
                <div class="timeline-content">
                    <span class="timeline-icon">${icon}</span>
                    <div class="timeline-info">
                        <div class="timeline-title">${txn.description || txn.source}</div>
                        <div class="timeline-date">${formatDate(txn.timestamp)}</div>
                    </div>
                    <div class="timeline-points ${isPositive ? 'positive' : 'negative'} ${txn.source === 'birthday' ? 'bonus' : ''}">
                        ${isPositive ? '+' : ''}${formatNumber(txn.points)} pts
                    </div>
                </div>
            </div>
        `;
  }).join('');
}

// ─── Handle Tier Upgrade ───
function handleTierUpgrade(event) {
  const { newTier, message } = event.detail;

  // Show confetti animation
  startConfetti();

  // Show tier upgrade modal
  setTimeout(() => {
    showTierUpgradeModal(newTier, message);
  }, 500);

  // Refresh UI components
  setTimeout(() => {
    renderTierProgress();
    renderTierBadges();
    renderAchievements();
  }, 1000);
}

// ─── Show Tier Upgrade Modal ───
function showTierUpgradeModal(newTier, message) {
  const modal = document.createElement('div');
  modal.className = 'tier-upgrade-modal';
  modal.id = 'tierUpgradeModal';
  modal.innerHTML = `
        <div class="tier-upgrade-content">
            <div class="tier-upgrade-icon">${newTier.icon}</div>
            <h2 class="tier-upgrade-title">🎉 Chúc Mừng!</h2>
            <p class="tier-upgrade-message">${message || `Bạn đã nâng hạng lên ${newTier.name}!`}</p>
            <div class="tier-upgrade-new-tier">
                <span class="tier-upgrade-new-tier-icon">${newTier.icon}</span>
                <span class="tier-upgrade-new-tier-name">${newTier.name}</span>
            </div>
            <button class="tier-upgrade-btn primary" id="closeTierModal">Tuyệt Vời!</button>
        </div>
    `;

  document.body.appendChild(modal);

  document.getElementById('closeTierModal').addEventListener('click', () => {
    modal.remove();
  });

  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.remove();
    }
  });
}

// ─── Start Confetti Animation ───
function startConfetti() {
  const container = document.createElement('div');
  container.className = 'confetti-container';
  container.id = 'confettiContainer';

  const colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#00e5ff', '#ff00ff', '#10b981', '#f59e0b'];
  const shapes = ['confetti-shape-rectangle', 'confetti-shape-circle', 'confetti-shape-triangle'];
  const confettiCount = 150;

  for (let i = 0; i < confettiCount; i++) {
    const confetti = document.createElement('div');
    confetti.className = `confetti ${shapes[Math.floor(Math.random() * shapes.length)]}`;
    confetti.style.left = `${Math.random() * 100}%`;
    confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    confetti.style.animationDelay = `${Math.random() * 0.5}s`;
    confetti.style.animationDuration = `${2 + Math.random() * 2}s`;
    container.appendChild(confetti);

    // Trigger animation
    setTimeout(() => {
      confetti.classList.add('active');
    }, 10);
  }

  document.body.appendChild(container);

  // Remove after animation
  setTimeout(() => {
    container.remove();
  }, 4000);
}

// ─── Render Rewards Grid ───
function renderRewards(category = 'all') {
  const rewards = getAvailableRewards(category);

  if (rewards.length === 0) {
    ui.rewardsGrid.innerHTML = `
            <div class="rewards-empty">
                <span class="empty-icon">🎁</span>
                <p>Chưa có rewards nào</p>
            </div>
        `;
    return;
  }

  ui.rewardsGrid.innerHTML = rewards.map(reward => {
    const canAfford = reward.canAfford;

    return `
            <div class="reward-card ${canAfford ? 'available' : 'locked'}" data-reward-id="${reward.id}">
                <div class="reward-image">
                    <img src="${reward.image || 'images/reward-placeholder.png'}" alt="${reward.name}" loading="lazy">
                    ${reward.badge ? `<span class="reward-badge">${reward.badge}</span>` : ''}
                </div>

                <div class="reward-content">
                    <div class="reward-header">
                        <h3 class="reward-name">${reward.name}</h3>
                        <div class="reward-points">
                            <span class="points-icon">🪙</span>
                            <span class="points-value">${formatNumber(reward.points)}</span>
                        </div>
                    </div>

                    <p class="reward-description">${reward.description}</p>

                    ${reward.terms ? `<p class="reward-terms">${reward.terms}</p>` : ''}

                    <div class="reward-progress">
                        <div class="progress-bar-mini">
                            <div class="progress-fill-mini" style="width: ${canAfford ? 100 : reward.progress}%"></div>
                        </div>
                        <span class="progress-text ${canAfford ? 'ready' : ''}">
                            ${canAfford ? '✓ Có thể đổi' : `${reward.progress}%`}
                        </span>
                    </div>

                    <button class="btn-redeem ${canAfford ? 'active' : ''}"
                            data-reward-id="${reward.id}"
                            ${!canAfford ? 'disabled' : ''}>
                        ${canAfford ? '🎁 Đổi Ngay' : '🔒 Tích Thêm'}
                    </button>
                </div>
            </div>
        `;
  }).join('');
}

// ─── Render Transactions ───
function renderTransactions() {
  const transactions = getTransactionHistory(15);

  if (transactions.length === 0) {
    ui.transactionsList.innerHTML = `
            <div class="history-empty">
                <span class="empty-icon">📜</span>
                <p>Chưa có giao dịch nào</p>
            </div>
        `;
    return;
  }

  ui.transactionsList.innerHTML = transactions.map(txn => {
    const isPositive = txn.points > 0;

    return `
            <div class="history-item ${isPositive ? 'earned' : 'spent'}">
                <div class="history-icon">${getTransactionIcon(txn.source || txn.type)}</div>
                <div class="history-content">
                    <span class="history-title">${txn.description || txn.source}</span>
                    <span class="history-date">${formatDate(txn.timestamp)}</span>
                </div>
                <div class="history-points ${isPositive ? 'positive' : 'negative'}">
                    ${isPositive ? '+' : ''}${formatNumber(txn.points)} pts
                </div>
            </div>
        `;
  }).join('');

  // Also update the timeline
  renderPointsTimeline();
}

// ─── Render Redemptions ───
function renderRedemptions() {
  const redemptions = getRedemptionHistory();

  if (redemptions.length === 0) {
    ui.redemptionsList.innerHTML = `
            <div class="history-empty">
                <span class="empty-icon">🎁</span>
                <p>Chưa đổi reward nào</p>
            </div>
        `;
    return;
  }

  ui.redemptionsList.innerHTML = redemptions.map(redemption => {
    const isExpired = new Date() > new Date(redemption.expiresAt);
    const statusClass = isExpired ? 'expired' : redemption.status;

    return `
            <div class="history-item redemption ${statusClass}">
                <div class="history-icon">🎁</div>
                <div class="history-content">
                    <span class="history-title">${redemption.rewardName}</span>
                    <span class="history-date">Đổi ${formatDate(redemption.redeemedAt)}</span>
                    ${isExpired ? '<span class="status-badge expired">Hết hạn</span>' : ''}
                </div>
                <div class="history-points negative">
                    -${formatNumber(redemption.pointsSpent)} pts
                </div>
            </div>
        `;
  }).join('');
}

// ─── Render Referral Code ───
function renderReferralCode() {
  const code = generateReferralCode();
  if (ui.referralCode) {ui.referralCode.textContent = code;}
  if (ui.referralCodeHero) {ui.referralCodeHero.textContent = code;}
}

// ─── Get Transaction Icon ───
function getTransactionIcon(source) {
  const icons = {
    purchase: '🛒',
    referral: '👥',
    tier_upgrade: '⬆️',
    tier_upgrade_bonus: '🎉',
    birthday: '🎂',
    review: '⭐',
    social_share: '📱',
    redeemed: '🎁'
  };
  return icons[source] || '📝';
}

// ─── Setup Event Listeners ───
function setupEventListeners() {
  // Rewards filter
  if (ui.rewardsFilter) {
    ui.rewardsFilter.addEventListener('click', (e) => {
      if (e.target.classList.contains('filter-btn')) {
        document.querySelectorAll('.rewards-filter .filter-btn').forEach(btn => {
          btn.classList.remove('active');
        });
        e.target.classList.add('active');
        renderRewards(e.target.dataset.category);
      }
    });
  }

  // Redeem button clicks (delegated)
  if (ui.rewardsGrid) {
    ui.rewardsGrid.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn-redeem');
      if (btn && btn.classList.contains('active')) {
        handleRedeemClick(btn.dataset.rewardId);
      }
    });
  }

  // History tabs
  ui.historyTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      ui.historyTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      document.querySelectorAll('.history-panel').forEach(panel => {
        panel.classList.remove('active');
      });

      const panelId = tab.dataset.tab + 'Panel';
      document.getElementById(panelId).classList.add('active');
    });
  });

  // Copy referral code (original)
  if (ui.copyReferralBtn) {
    ui.copyReferralBtn.addEventListener('click', () => {
      const code = ui.referralCode.textContent;
      navigator.clipboard.writeText(code);
      showToast('📋 Đã sao chép mã giới thiệu!', 'success');
    });
  }

  // Copy referral code (hero)
  if (ui.copyReferralBtnHero) {
    ui.copyReferralBtnHero.addEventListener('click', () => {
      const code = ui.referralCodeHero.textContent;
      navigator.clipboard.writeText(code);
      showToast('📋 Đã sao chép mã giới thiệu!', 'success');
    });
  }

  // Share via Zalo
  if (ui.shareZalo) {
    ui.shareZalo.addEventListener('click', () => {
      const code = ui.referralCodeHero.textContent;
      const message = encodeURIComponent(`🎁 F&B Container - Giới thiệu bạn bè\n\nNhận ngay 200 points khi bạn tham gia chương trình loyalty!\n\nMã giới thiệu: ${code}\n\nGhé ngay: https://fnbcontainer.vn/loyalty`);
      window.open(`https://zalo.me/share?text=${message}`, '_blank');
    });
  }

  // Share via Facebook
  if (ui.shareFacebook) {
    ui.shareFacebook.addEventListener('click', () => {
      const url = encodeURIComponent('https://fnbcontainer.vn/loyalty');
      window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank');
    });
  }

  // Share copy & send
  if (ui.shareCopy) {
    ui.shareCopy.addEventListener('click', async () => {
      const code = ui.referralCodeHero.textContent;
      const shareText = `🎁 F&B Container - Giới thiệu bạn bè\n\nNhận ngay 200 points khi bạn tham gia chương trình loyalty!\n\nMã giới thiệu: ${code}\n\nGhé ngay: https://fnbcontainer.vn/loyalty`;
      try {
        await navigator.clipboard.writeText(shareText);
        showToast('📋 Đã sao chép! Giờ bạn có thể gửi cho bạn bè', 'success');
      } catch (err) {
        showToast('⚠️ Không thể sao chép', 'error');
      }
    });
  }

  // Modal close
  if (ui.modalClose) {
    ui.modalClose.addEventListener('click', closeModal);
    ui.redemptionModal.addEventListener('click', (e) => {
      if (e.target === ui.redemptionModal) {closeModal();}
    });
  }

  // Keyboard escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {closeModal();}
  });
}

// ─── Handle Redeem Click ───
function handleRedeemClick(rewardId) {
  const rewards = window.LoyaltySystem?.config?.rewards || [];
  const reward = rewards.find(r => r.id === rewardId);

  if (!reward) {return;}

  // Show confirmation modal
  ui.redemptionModalBody.innerHTML = `
        <div class="reward-confirm-header">
            <span class="confirm-icon">🎁</span>
            <h2>Xác Nhận Đổi Thưởng</h2>
        </div>

        <div class="reward-confirm-body">
            <div class="confirm-reward-info">
                <h3>${reward.name}</h3>
                <p>${reward.description}</p>
            </div>

            <div class="confirm-points-row">
                <span>Điểm cần thiết:</span>
                <strong class="points-highlight">${formatNumber(reward.points)} points</strong>
            </div>

            <div class="confirm-terms">
                <p><strong>Điều khoản:</strong> ${reward.terms}</p>
                ${reward.expiryDays ? `<p><strong>Hạn sử dụng:</strong> ${reward.expiryDays} ngày</p>` : ''}
            </div>
        </div>

        <div class="confirm-actions">
            <button class="btn-cancel" id="cancelRedeemBtn">Hủy</button>
            <button class="btn-confirm" id="confirmRedeemBtn">✓ Xác Nhận Đổi</button>
        </div>
    `;

  ui.redemptionModal.style.display = 'flex';

  // Setup confirm/cancel handlers
  document.getElementById('cancelRedeemBtn').addEventListener('click', closeModal);
  document.getElementById('confirmRedeemBtn').addEventListener('click', () => {
    confirmRedemption(rewardId);
  });
}

// ─── Confirm Redemption ───
function confirmRedemption(rewardId) {
  const result = redeemReward(rewardId);

  if (result.success) {
    showToast(`🎉 Đã đổi ${result.redemption.rewardName} thành công!`, 'success');
    closeModal();

    // Refresh UI
    renderRewards();
    renderTransactions();
    renderRedemptions();
    renderLoyaltyCard();
  } else {
    showToast(`⚠️ ${result.error}`, 'error');
    closeModal();
  }
}

// ─── Close Modal ───
function closeModal() {
  if (ui.redemptionModal) {
    ui.redemptionModal.style.display = 'none';
  }
}

// ─── Show Toast Notification ───
function showToast(message, type = 'info') {
  if (!ui.toastContainer) {return;}

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
        <span class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '⚠️' : 'ℹ️'}</span>
        <span class="toast-message">${message}</span>
    `;

  ui.toastContainer.appendChild(toast);

  // Animate in
  setTimeout(() => toast.classList.add('show'), 10);

  // Auto remove
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ─── Format Number ───
function formatNumber(num) {
  return new Intl.NumberFormat('vi-VN').format(num);
}

// ─── Format Date ───
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// ─── Export for debugging ───
window.LoyaltyUI = {
  refresh: initLoyaltyUI,
  renderRewards,
  renderTransactions,
  renderRedemptions,
  renderAchievements,
  renderPointsTimeline,
  showToast,
  startConfetti,
  handleTierUpgrade
};

// ─── Dark Mode Theme Toggle ───
function initThemeToggle() {
  if (!ui.themeToggle) {return;}

  const themeIcon = ui.themeToggle.querySelector('.theme-icon');
  const savedTheme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);

  if (themeIcon) {
    themeIcon.textContent = savedTheme === 'dark' ? '🌙' : '☀️';
  }

  ui.themeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    if (themeIcon) {
      themeIcon.textContent = newTheme === 'dark' ? '🌙' : '☀️';
    }
  });
}
