/**
 * Priya Shopping Assistant — Family Dashboard Logic
 * Uses safe DOM manipulation (textContent / createElement) without unsafe innerHTML.
 */

(function () {
  'use strict';

  let currentProfileId = null;

  const el = {
    loginSection: document.getElementById('login-section'),
    dashboardContent: document.getElementById('dashboard-content'),
    authHeaderLoggedIn: document.getElementById('auth-header-logged-in'),
    userDisplayName: document.getElementById('user-display-name'),
    loginForm: document.getElementById('login-form'),
    usernameInput: document.getElementById('username'),
    passwordInput: document.getElementById('password'),
    btnLogin: document.getElementById('btn-login'),
    btnLogout: document.getElementById('btn-logout'),
    statusMessage: document.getElementById('status-message'),
    elderName: document.getElementById('elder-name'),
    elderPhone: document.getElementById('elder-phone'),
    elderLang: document.getElementById('elder-lang'),
    elderAddress: document.getElementById('elder-address'),
    elderLimit: document.getElementById('elder-limit'),
    elderApprovalRule: document.getElementById('elder-approval-rule'),
    newLimit: document.getElementById('new-limit'),
    requireApprovalChk: document.getElementById('require-approval-chk'),
    policyForm: document.getElementById('policy-form'),
    pendingCountBadge: document.getElementById('pending-count-badge'),
    noPendingMsg: document.getElementById('no-pending-msg'),
    pendingOrdersList: document.getElementById('pending-orders-list'),
    ordersTableBody: document.getElementById('orders-table-body'),
    auditTableBody: document.getElementById('audit-table-body'),
    btnRefreshOrders: document.getElementById('btn-refresh-orders'),
  };

  function showStatus(msg, type = 'error') {
    el.statusMessage.className = `status-message ${type}`;
    el.statusMessage.textContent = msg;
    el.statusMessage.classList.remove('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function hideStatus() {
    el.statusMessage.classList.add('hidden');
    el.statusMessage.textContent = '';
  }

  function formatINR(amount) {
    return '₹' + Number(amount).toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  // Check login state
  async function checkAuth() {
    try {
      const res = await fetch('/api/v1/family/auth/me');
      if (res.ok) {
        const user = await res.json();
        onAuthenticated(user);
      } else {
        onLoggedOut();
      }
    } catch {
      onLoggedOut();
    }
  }

  function onAuthenticated(user) {
    el.loginSection.classList.add('hidden');
    el.dashboardContent.classList.remove('hidden');
    el.authHeaderLoggedIn.classList.remove('hidden');
    el.userDisplayName.textContent = `${user.full_name} (${user.role})`;
    loadDashboardData();
  }

  function onLoggedOut() {
    el.loginSection.classList.remove('hidden');
    el.dashboardContent.classList.add('hidden');
    el.authHeaderLoggedIn.classList.add('hidden');
  }

  // Handle Login
  async function handleLogin() {
    hideStatus();
    el.btnLogin.disabled = true;

    try {
      const res = await fetch('/api/v1/family/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: el.usernameInput.value.trim(),
          password: el.passwordInput.value,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Sign-in failed.');
      }

      const user = await res.json();
      onAuthenticated(user);
    } catch (e) {
      showStatus(e.message);
    } finally {
      el.btnLogin.disabled = false;
    }
  }

  // Handle Logout
  async function handleLogout() {
    await fetch('/api/v1/family/auth/logout', { method: 'POST' });
    onLoggedOut();
  }

  // Load Dashboard Data
  async function loadDashboardData() {
    hideStatus();
    try {
      // 1. Load Elder Profile
      const profRes = await fetch('/api/v1/family/profiles');
      if (profRes.ok) {
        const profiles = await profRes.json();
        if (profiles.length > 0) {
          const p = profiles[0];
          currentProfileId = p.id;
          el.elderName.textContent = p.display_name;
          el.elderPhone.textContent = p.phone_number || 'N/A';
          el.elderLang.textContent = p.preferred_language.toUpperCase();
          el.elderAddress.textContent = p.delivery_address || 'None saved';
          el.elderLimit.textContent = formatINR(p.spending_limit_inr);
          el.elderApprovalRule.textContent = p.family_approval_required ? 'Required for all orders' : 'Only if exceeding limit';

          el.newLimit.value = p.spending_limit_inr;
          el.requireApprovalChk.checked = p.family_approval_required;
        }
      }

      // 2. Load Orders
      await loadOrders();

      // 3. Load Audit Log
      await loadAuditLogs();
    } catch (e) {
      showStatus('Failed to load dashboard data: ' + e.message);
    }
  }

  // Load Orders & Pending Approvals
  async function loadOrders() {
    const res = await fetch('/api/v1/family/orders');
    if (!res.ok) return;

    const orders = await res.json();
    el.ordersTableBody.textContent = '';
    el.pendingOrdersList.textContent = '';

    const pendingOrders = orders.filter((o) => o.status === 'awaiting_family_approval');
    el.pendingCountBadge.textContent = `${pendingOrders.length} pending`;

    if (pendingOrders.length === 0) {
      el.noPendingMsg.classList.remove('hidden');
    } else {
      el.noPendingMsg.classList.add('hidden');
      pendingOrders.forEach((o) => {
        const itemBox = document.createElement('div');
        itemBox.style.cssText = 'background: #fffbeb; border: 2px solid #f59e0b; padding: 1rem; border-radius: var(--radius-md);';

        const head = document.createElement('div');
        head.style.cssText = 'display: flex; justify-content: space-between; font-weight: 700; margin-bottom: 0.5rem;';
        head.textContent = `Order: ${o.id}`;
        
        const totalTag = document.createElement('span');
        totalTag.style.color = '#b45309';
        totalTag.textContent = formatINR(o.total_inr);
        head.appendChild(totalTag);
        itemBox.appendChild(head);

        const itemsDesc = document.createElement('p');
        itemsDesc.style.fontSize = 'var(--font-size-sm)';
        itemsDesc.style.color = 'var(--color-text-muted)';
        const names = (o.quote_snapshot && o.quote_snapshot.items)
          ? o.quote_snapshot.items.map((i) => `${i.quantity}x ${i.name}`).join(', ')
          : `${o.items_count} item(s)`;
        itemsDesc.textContent = `Items: ${names}`;
        itemBox.appendChild(itemsDesc);

        const actions = document.createElement('div');
        actions.style.cssText = 'display: flex; gap: 0.5rem; margin-top: 0.75rem;';

        const btnApprove = document.createElement('button');
        btnApprove.type = 'button';
        btnApprove.className = 'btn btn-success';
        btnApprove.style.cssText = 'min-height: 38px; padding: 0.4rem 0.8rem;';
        btnApprove.textContent = '✅ Approve Order';
        btnApprove.addEventListener('click', () => actionOrder(o.id, true));
        actions.appendChild(btnApprove);

        const btnReject = document.createElement('button');
        btnReject.type = 'button';
        btnReject.className = 'btn btn-outline';
        btnReject.style.cssText = 'min-height: 38px; padding: 0.4rem 0.8rem; color: #b91c1c; border-color: #ef4444;';
        btnReject.textContent = '❌ Reject';
        btnReject.addEventListener('click', () => actionOrder(o.id, false));
        actions.appendChild(btnReject);

        itemBox.appendChild(actions);
        el.pendingOrdersList.appendChild(itemBox);
      });
    }

    // Render Order History Table
    orders.forEach((o) => {
      const tr = document.createElement('tr');

      const tdId = document.createElement('td');
      tdId.textContent = o.id;
      tr.appendChild(tdId);

      const tdDate = document.createElement('td');
      tdDate.textContent = new Date(o.created_at).toLocaleDateString();
      tr.appendChild(tdDate);

      const tdItems = document.createElement('td');
      tdItems.textContent = `${o.items_count} items`;
      tr.appendChild(tdItems);

      const tdTotal = document.createElement('td');
      const strongTotal = document.createElement('strong');
      strongTotal.textContent = formatINR(o.total_inr);
      tdTotal.appendChild(strongTotal);
      tr.appendChild(tdTotal);

      const tdStatus = document.createElement('td');
      const badge = document.createElement('span');
      badge.className = `badge-status status-${o.status}`;
      badge.textContent = o.status;
      tdStatus.appendChild(badge);
      tr.appendChild(tdStatus);

      const tdAction = document.createElement('td');
      const codePreview = document.createElement('code');
      codePreview.style.fontSize = '0.75rem';
      codePreview.textContent = o.preview_id;
      tdAction.appendChild(codePreview);
      tr.appendChild(tdAction);

      el.ordersTableBody.appendChild(tr);
    });
  }

  // Approve or Reject an Order
  async function actionOrder(orderId, isApproved) {
    hideStatus();
    const endpoint = isApproved ? 'approve' : 'reject';
    try {
      const res = await fetch(`/api/v1/family/orders/${orderId}/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason_note: isApproved ? 'Approved by guardian' : 'Rejected by guardian' }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Action failed.');
      }

      showStatus(`Order ${orderId} ${isApproved ? 'approved' : 'rejected'} successfully!`, 'success');
      loadDashboardData();
    } catch (e) {
      showStatus(e.message);
    }
  }

  // Update Policy
  async function handlePolicyUpdate() {
    if (!currentProfileId) return;
    hideStatus();

    try {
      const newLimitVal = parseFloat(el.newLimit.value);
      const reqApproval = el.requireApprovalChk.checked;

      const res = await fetch(`/api/v1/family/profiles/${currentProfileId}/policy`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          spending_limit_inr: newLimitVal,
          family_approval_required: reqApproval,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to update policy.');
      }

      showStatus('Spending limits and approval policy updated successfully!', 'success');
      loadDashboardData();
    } catch (e) {
      showStatus(e.message);
    }
  }

  // Load Audit Logs
  async function loadAuditLogs() {
    const res = await fetch('/api/v1/family/audit-events');
    if (!res.ok) return;

    const events = await res.json();
    el.auditTableBody.textContent = '';

    events.forEach((ev) => {
      const tr = document.createElement('tr');

      const tdTime = document.createElement('td');
      tdTime.textContent = new Date(ev.created_at).toLocaleTimeString();
      tr.appendChild(tdTime);

      const tdActor = document.createElement('td');
      tdActor.textContent = ev.actor_type;
      tr.appendChild(tdActor);

      const tdAction = document.createElement('td');
      const badge = document.createElement('span');
      badge.style.cssText = 'background: #f1f5f9; padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: 600;';
      badge.textContent = ev.action;
      tdAction.appendChild(badge);
      tr.appendChild(tdAction);

      const tdTarget = document.createElement('td');
      tdTarget.textContent = `${ev.target_type} (${ev.target_id || ''})`;
      tr.appendChild(tdTarget);

      const tdDetails = document.createElement('td');
      tdDetails.style.fontSize = '0.75rem';
      tdDetails.textContent = JSON.stringify(ev.details || {});
      tr.appendChild(tdDetails);

      el.auditTableBody.appendChild(tr);
    });
  }

  // Setup Event Listeners
  document.addEventListener('DOMContentLoaded', () => {
    el.loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleLogin();
    });

    el.btnLogout.addEventListener('click', handleLogout);

    el.policyForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handlePolicyUpdate();
    });

    el.btnRefreshOrders.addEventListener('click', loadOrders);

    checkAuth();
  });
})();
