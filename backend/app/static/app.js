/**
 * Priya Shopping Assistant — Local Demo Frontend Logic
 * Strictly uses safe DOM manipulation (textContent / createElement) without unsafe innerHTML.
 */

(function () {
  'use strict';

  // Application State
  const state = {
    lang: 'en',
    cart: new Map(), // product_id -> { product, quantity }
    activePreview: null,
    confirmedOrder: null,
    isSearching: false,
    isPreviewing: false,
    isConfirming: false,
  };

  // Translations dictionary for bilingual support (English / Hindi)
  const i18n = {
    en: {
      appTitle: 'Priya Shopping Assistant — Local Demo',
      appSubtitle: 'Voice & Text Shopping for Indian Seniors',
      warningTitle: 'Demo only',
      warningDesc: 'Products, prices, availability, and orders are sample data. No real order or payment will be made.',
      searchHeading: '1. Search Products / उत्पाद खोजें',
      lblSearchInput: 'What would you like to buy today?',
      searchPlaceholder: 'e.g. reading glasses, senior phone, shoes, BP monitor',
      btnSearch: 'Search',
      lblCategory: 'Category (Optional)',
      lblMaxPrice: 'Max Price (₹ INR, Optional)',
      btnReset: 'Reset Filters',
      lblExamples: 'Try asking:',
      resultsHeading: 'Search Results / खोज परिणाम',
      lblLoading: 'Searching mock catalogue...',
      lblEmptyPrompt: 'Enter a search query or click one of the suggestions above to view products.',
      lblEmptyNoMatch: 'No matching products found in the mock catalogue. Try another keyword like "glasses" or "phone".',
      previewHeading: '2. Order Preview / ऑर्डर पूर्वावलोकन',
      lblCartEmpty: 'No items added to preview yet. Choose products from the results list on the left.',
      colItem: 'Item',
      colQty: 'Qty',
      colPrice: 'Price',
      colTotal: 'Total',
      colAction: 'Action',
      lblSubtotal: 'Subtotal (INR):',
      lblGrandtotal: 'Grand Total (INR):',
      lblSummaryNote: '* Fictional demo total calculated authoritatively by the backend.',
      btnReview: 'Review / Refresh Preview',
      btnClearCart: 'Clear All',
      lblPreviewInstruction: 'Please verify your demo order items and total above. When ready, click the button below to confirm.',
      btnConfirm: 'Confirm Demo Order',
      lblConfirmSubtext: 'Confirmation requires this explicit click. No charge or real transaction will take place.',
      lblOrderSuccess: 'Demo Order Placed Successfully!',
      lblOrderRefText: 'Demo Reference ID:',
      lblStatusLabel: 'Status:',
      lblConfirmedTime: 'Timestamp:',
      lblFinalAmount: 'Total Demo Amount:',
      lblNotice: 'Important Notice:',
      lblNoticeBody: 'This order is stored in-memory for testing only and will be reset when the local server restarts. No real store was contacted.',
      btnNewOrder: 'Start Another Search',
      footerPhase: 'Priya Shopping Assistant — Phase 1 Local Vertical Slice',
      footerSub: 'Bound strictly to 127.0.0.1 • Fast, Accessible, Senior-Friendly Design',
      inStock: 'In Stock (Demo)',
      addToPreview: 'Add to Preview',
      remove: 'Remove',
    },
    hi: {
      appTitle: 'प्रिया शॉपिंग असिस्टेंट — लोकल डेमो',
      appSubtitle: 'भारतीय वरिष्ठ नागरिकों के लिए बोलकर या लिखकर खरीदारी',
      warningTitle: 'केवल डेमो',
      warningDesc: 'उत्पाद, कीमतें, उपलब्धता और ऑर्डर केवल नमूना डेटा हैं। कोई वास्तविक ऑर्डर या भुगतान नहीं होगा।',
      searchHeading: '1. उत्पाद खोजें (Search Products)',
      lblSearchInput: 'आज आप क्या खरीदना चाहेंगे?',
      searchPlaceholder: 'जैसे: चश्मा, बुजुर्गों का फोन, जूते, बीपी मशीन',
      btnSearch: 'खोजें',
      lblCategory: 'श्रेणी (वैकल्पिक)',
      lblMaxPrice: 'अधिकतम मूल्य (₹ रुपये, वैकल्पिक)',
      btnReset: 'फ़िल्टर हटाएं',
      lblExamples: 'सुझाव देखें:',
      resultsHeading: 'खोज परिणाम (Results)',
      lblLoading: 'कैटलॉग में खोजा जा रहा है...',
      lblEmptyPrompt: 'कृपया कोई खोज शब्द लिखें या ऊपर दिए गए सुझावों पर क्लिक करें।',
      lblEmptyNoMatch: 'इस शब्द से कोई उत्पाद नहीं मिला। कृपया "चश्मा" या "फोन" जैसे सरल शब्द आज़माएं।',
      previewHeading: '2. ऑर्डर पूर्वावलोकन (Order Preview)',
      lblCartEmpty: 'पूर्वावलोकन के लिए कोई वस्तु नहीं चुनी गई है। बाईं ओर से उत्पाद चुनें।',
      colItem: 'उत्पाद',
      colQty: 'मात्रा',
      colPrice: 'कीमत',
      colTotal: 'कुल',
      colAction: 'हटाएं',
      lblSubtotal: 'उप-कुल (INR):',
      lblGrandtotal: 'कुल राशि (INR):',
      lblSummaryNote: '* यह केवल डेमो राशि है जिसकी गणना बैकएंड द्वारा की गई है।',
      btnReview: 'पूर्वावलोकन जांचें',
      btnClearCart: 'सब हटाएं',
      lblPreviewInstruction: 'कृपया ऊपर अपने ऑर्डर की वस्तुएं और कुल राशि जांच लें। संतुष्ट होने पर नीचे पुष्टि बटन दबाएं।',
      btnConfirm: 'डेमो ऑर्डर की पुष्टि करें',
      lblConfirmSubtext: 'पुष्टि के लिए इस बटन पर क्लिक करना अनिवार्य है। कोई असली भुगतान नहीं काटा जाएगा।',
      lblOrderSuccess: 'डेमो ऑर्डर सफलतापूर्वक दर्ज हुआ!',
      lblOrderRefText: 'डेमो संदर्भ संख्या (Order ID):',
      lblStatusLabel: 'स्थिति:',
      lblConfirmedTime: 'समय:',
      lblFinalAmount: 'कुल डेमो राशि:',
      lblNotice: 'महत्वपूर्ण सूचना:',
      lblNoticeBody: 'यह ऑर्डर केवल इस परीक्षण सत्र के लिए मेमोरी में सुरक्षित है और सर्वर बंद होने पर रीसेट हो जाएगा।',
      btnNewOrder: 'नया ऑर्डर शुरू करें',
      footerPhase: 'प्रिया शॉपिंग असिस्टेंट — फेज़ 1 लोकल वर्टिकल स्लाइस',
      footerSub: 'केवल 127.0.0.1 पर उपलब्ध • बुजुर्गों के लिए स्पष्ट व सुरक्षित डिज़ाइन',
      inStock: 'उपलब्ध है',
      addToPreview: 'ऑर्डर में जोड़ें',
      remove: 'हटाएं',
    },
  };

  // DOM Elements
  const el = {
    langSelect: document.getElementById('lang-select'),
    searchForm: document.getElementById('search-form'),
    searchInput: document.getElementById('search-input'),
    btnSearch: document.getElementById('btn-search'),
    btnSearchText: document.getElementById('btn-search-text'),
    filterCategory: document.getElementById('filter-category'),
    filterMaxPrice: document.getElementById('filter-max-price'),
    btnClearFilters: document.getElementById('btn-clear-filters'),
    chipsContainer: document.getElementById('chips-container'),
    statusMessage: document.getElementById('status-message'),
    resultsContainer: document.getElementById('results-container'),
    resultsLoading: document.getElementById('results-loading'),
    resultsEmpty: document.getElementById('results-empty'),
    resultsCount: document.getElementById('results-count'),
    cartItemCount: document.getElementById('cart-item-count'),
    cartEmptyMessage: document.getElementById('cart-empty-message'),
    cartItemsCard: document.getElementById('cart-items-card'),
    cartTableBody: document.getElementById('cart-table-body'),
    summarySubtotal: document.getElementById('summary-subtotal'),
    summaryTotal: document.getElementById('summary-total'),
    btnRequestPreview: document.getElementById('btn-request-preview'),
    btnClearCart: document.getElementById('btn-clear-cart'),
    serverPreviewBox: document.getElementById('server-preview-box'),
    displayPreviewId: document.getElementById('display-preview-id'),
    btnConfirmOrder: document.getElementById('btn-confirm-order'),
    confirmedCard: document.getElementById('confirmed-card'),
    displayOrderId: document.getElementById('display-order-id'),
    displayOrderTime: document.getElementById('display-order-time'),
    displayOrderTotal: document.getElementById('display-order-total'),
    btnNewOrder: document.getElementById('btn-new-order'),
  };

  function updateLanguage(lang) {
    state.lang = lang;
    const t = i18n[lang];
    if (!t) return;

    // Update static text elements safely using textContent
    document.getElementById('app-title').textContent = t.appTitle;
    document.getElementById('app-subtitle').textContent = t.appSubtitle;
    document.getElementById('warning-title').textContent = t.warningTitle;
    document.getElementById('warning-desc').textContent = t.warningDesc;
    document.getElementById('search-heading').textContent = t.searchHeading;
    document.getElementById('lbl-search-input').textContent = t.lblSearchInput;
    el.searchInput.placeholder = t.searchPlaceholder;
    el.btnSearchText.textContent = t.btnSearch;
    document.getElementById('lbl-category').textContent = t.lblCategory;
    document.getElementById('lbl-max-price').textContent = t.lblMaxPrice;
    document.getElementById('btn-clear-text').textContent = t.btnReset;
    document.getElementById('lbl-examples').textContent = t.lblExamples;
    document.getElementById('results-heading').textContent = t.resultsHeading;
    document.getElementById('lbl-loading').textContent = t.lblLoading;
    document.getElementById('lbl-empty-prompt').textContent = t.lblEmptyPrompt;
    document.getElementById('preview-heading').textContent = t.previewHeading;
    document.getElementById('lbl-cart-empty').textContent = t.lblCartEmpty;
    document.getElementById('col-item').textContent = t.colItem;
    document.getElementById('col-qty').textContent = t.colQty;
    document.getElementById('col-price').textContent = t.colPrice;
    document.getElementById('col-total').textContent = t.colTotal;
    document.getElementById('col-action').textContent = t.colAction;
    document.getElementById('lbl-subtotal').textContent = t.lblSubtotal;
    document.getElementById('lbl-grandtotal').textContent = t.lblGrandtotal;
    document.getElementById('lbl-summary-note').textContent = t.lblSummaryNote;
    document.getElementById('btn-review-text').textContent = t.btnReview;
    document.getElementById('btn-clear-cart-text').textContent = t.btnClearCart;
    document.getElementById('lbl-preview-instruction').textContent = t.lblPreviewInstruction;
    document.getElementById('btn-confirm-text').textContent = t.btnConfirm;
    document.getElementById('lbl-confirm-subtext').textContent = t.lblConfirmSubtext;
    document.getElementById('lbl-order-success').textContent = t.lblOrderSuccess;
    document.getElementById('lbl-order-ref-text').textContent = t.lblOrderRefText;
    document.getElementById('lbl-status-label').textContent = t.lblStatusLabel;
    document.getElementById('lbl-confirmed-time').textContent = t.lblConfirmedTime;
    document.getElementById('lbl-final-amount').textContent = t.lblFinalAmount;
    document.getElementById('lbl-notice').textContent = t.lblNotice;
    document.getElementById('lbl-notice-body').textContent = t.lblNoticeBody;
    document.getElementById('btn-new-order-text').textContent = t.btnNewOrder;
    document.getElementById('footer-phase').textContent = t.footerPhase;
    document.getElementById('footer-sub').textContent = t.footerSub;
  }

  function showStatus(message, type = 'error') {
    el.statusMessage.className = `status-message ${type}`;
    el.statusMessage.textContent = message;
    el.statusMessage.classList.remove('hidden');
    window.scrollTo({ top: el.statusMessage.offsetTop - 80, behavior: 'smooth' });
  }

  function hideStatus() {
    el.statusMessage.classList.add('hidden');
    el.statusMessage.textContent = '';
  }

  // Format currency
  function formatINR(amount) {
    return '₹' + Number(amount).toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  // Perform Product Search
  async function performSearch(query, category = null, maxPrice = null) {
    if (!query || !query.trim()) {
      showStatus(state.lang === 'hi' ? 'कृपया खोज के लिए कुछ लिखें।' : 'Please enter a search query.');
      return;
    }

    hideStatus();
    state.isSearching = true;
    el.btnSearch.disabled = true;
    el.resultsLoading.classList.remove('hidden');
    el.resultsEmpty.classList.add('hidden');
    el.resultsContainer.textContent = ''; // safe clear

    try {
      const payload = {
        query: query.trim(),
        limit: 5,
      };
      if (category && category.trim()) {
        payload.category = category.trim();
      }
      if (maxPrice !== null && !isNaN(maxPrice) && maxPrice > 0) {
        payload.max_price = parseFloat(maxPrice);
      }

      const response = await fetch('/api/v1/products/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Search failed with status ${response.status}`);
      }

      const data = await response.json();
      renderSearchResults(data.matches || []);
    } catch (err) {
      showStatus(err.message || 'An error occurred while searching products.');
      el.resultsEmpty.classList.remove('hidden');
      document.getElementById('lbl-empty-prompt').textContent = i18n[state.lang].lblEmptyNoMatch;
    } finally {
      state.isSearching = false;
      el.btnSearch.disabled = false;
      el.resultsLoading.classList.add('hidden');
    }
  }

  // Render Product Search Results Safely using DOM methods
  function renderSearchResults(products) {
    el.resultsContainer.textContent = '';
    const t = i18n[state.lang];

    el.resultsCount.textContent = `${products.length} found`;

    if (!products || products.length === 0) {
      el.resultsEmpty.classList.remove('hidden');
      document.getElementById('lbl-empty-prompt').textContent = t.lblEmptyNoMatch;
      return;
    }

    el.resultsEmpty.classList.add('hidden');

    products.forEach((product) => {
      const card = document.createElement('div');
      card.className = 'product-card';

      // Top row
      const cardTop = document.createElement('div');
      cardTop.className = 'product-card-top';

      const titleWrap = document.createElement('div');
      const title = document.createElement('h3');
      title.className = 'product-title';
      title.textContent = product.name;
      titleWrap.appendChild(title);

      if (product.name_hi) {
        const titleHi = document.createElement('div');
        titleHi.className = 'product-title-hi';
        titleHi.textContent = product.name_hi;
        titleWrap.appendChild(titleHi);
      }
      cardTop.appendChild(titleWrap);

      const categoryTag = document.createElement('span');
      categoryTag.className = 'category-tag';
      categoryTag.textContent = product.category;
      cardTop.appendChild(categoryTag);

      card.appendChild(cardTop);

      // Description
      const desc = document.createElement('p');
      desc.className = 'product-desc';
      desc.textContent = state.lang === 'hi' && product.description_hi ? product.description_hi : product.description;
      card.appendChild(desc);

      // Bottom row
      const cardBottom = document.createElement('div');
      cardBottom.className = 'product-card-bottom';

      const priceWrap = document.createElement('div');
      const priceTag = document.createElement('span');
      priceTag.className = 'price-tag';
      priceTag.textContent = formatINR(product.price_inr);
      priceWrap.appendChild(priceTag);

      const stockBadge = document.createElement('span');
      stockBadge.className = 'stock-badge';
      stockBadge.textContent = t.inStock;
      priceWrap.appendChild(document.createTextNode(' '));
      priceWrap.appendChild(stockBadge);
      cardBottom.appendChild(priceWrap);

      // Action controls
      const actions = document.createElement('div');
      actions.className = 'card-actions';

      const qtySelect = document.createElement('select');
      qtySelect.className = 'qty-select';
      qtySelect.setAttribute('aria-label', `Quantity for ${product.name}`);
      for (let q = 1; q <= 5; q++) {
        const opt = document.createElement('option');
        opt.value = String(q);
        opt.textContent = `${q} ${product.unit || 'unit'}`;
        qtySelect.appendChild(opt);
      }
      actions.appendChild(qtySelect);

      const addBtn = document.createElement('button');
      addBtn.type = 'button';
      addBtn.className = 'btn btn-primary';
      addBtn.textContent = `+ ${t.addToPreview}`;
      addBtn.addEventListener('click', () => {
        const selectedQty = parseInt(qtySelect.value, 10) || 1;
        addToCart(product, selectedQty);
      });
      actions.appendChild(addBtn);

      cardBottom.appendChild(actions);
      card.appendChild(cardBottom);

      el.resultsContainer.appendChild(card);
    });
  }

  // Cart operations
  function addToCart(product, quantity) {
    hideStatus();
    const existing = state.cart.get(product.id);
    const newQty = existing ? existing.quantity + quantity : quantity;
    if (newQty > 10) {
      showStatus('Maximum 10 units allowed per item in this demo.');
      return;
    }
    state.cart.set(product.id, { product, quantity: newQty });
    // Invalidate any previously active preview since cart changed
    state.activePreview = null;
    el.serverPreviewBox.classList.add('hidden');
    renderCart();
  }

  function removeFromCart(productId) {
    hideStatus();
    state.cart.delete(productId);
    state.activePreview = null;
    el.serverPreviewBox.classList.add('hidden');
    renderCart();
  }

  function clearCart() {
    hideStatus();
    state.cart.clear();
    state.activePreview = null;
    el.serverPreviewBox.classList.add('hidden');
    renderCart();
  }

  function renderCart() {
    const t = i18n[state.lang];
    el.cartTableBody.textContent = '';
    const totalItems = Array.from(state.cart.values()).reduce((sum, item) => sum + item.quantity, 0);
    el.cartItemCount.textContent = `${totalItems} items`;

    if (state.cart.size === 0) {
      el.cartEmptyMessage.classList.remove('hidden');
      el.cartItemsCard.classList.add('hidden');
      el.serverPreviewBox.classList.add('hidden');
      return;
    }

    el.cartEmptyMessage.classList.add('hidden');
    el.cartItemsCard.classList.remove('hidden');

    let localSubtotal = 0;

    state.cart.forEach(({ product, quantity }) => {
      const lineTotal = product.price_inr * quantity;
      localSubtotal += lineTotal;

      const row = document.createElement('tr');

      // Item Name
      const tdItem = document.createElement('td');
      const itemTitle = document.createElement('strong');
      itemTitle.textContent = state.lang === 'hi' && product.name_hi ? product.name_hi : product.name;
      tdItem.appendChild(itemTitle);
      row.appendChild(tdItem);

      // Quantity
      const tdQty = document.createElement('td');
      tdQty.textContent = String(quantity);
      row.appendChild(tdQty);

      // Unit Price
      const tdPrice = document.createElement('td');
      tdPrice.textContent = formatINR(product.price_inr);
      row.appendChild(tdPrice);

      // Line Total
      const tdTotal = document.createElement('td');
      tdTotal.textContent = formatINR(lineTotal);
      row.appendChild(tdTotal);

      // Action: Remove
      const tdAction = document.createElement('td');
      const rmBtn = document.createElement('button');
      rmBtn.type = 'button';
      rmBtn.className = 'btn-danger-sm';
      rmBtn.textContent = t.remove;
      rmBtn.addEventListener('click', () => removeFromCart(product.id));
      tdAction.appendChild(rmBtn);
      row.appendChild(tdAction);

      el.cartTableBody.appendChild(row);
    });

    el.summarySubtotal.textContent = formatINR(localSubtotal);
    el.summaryTotal.textContent = formatINR(localSubtotal);
  }

  // Request Backend Preview
  async function requestOrderPreview() {
    if (state.cart.size === 0) {
      showStatus('Please add at least one product before reviewing an order.');
      return;
    }

    hideStatus();
    state.isPreviewing = true;
    el.btnRequestPreview.disabled = true;

    try {
      const itemsPayload = Array.from(state.cart.values()).map(({ product, quantity }) => ({
        product_id: product.id,
        quantity: quantity,
      }));

      const response = await fetch('/api/v1/orders/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: itemsPayload }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Preview creation failed with status ${response.status}`);
      }

      const previewData = await response.json();
      state.activePreview = previewData;

      // Update displayed preview data
      el.displayPreviewId.textContent = previewData.preview_id;
      el.summarySubtotal.textContent = formatINR(previewData.subtotal_inr);
      el.summaryTotal.textContent = formatINR(previewData.total_inr);

      el.serverPreviewBox.classList.remove('hidden');
      el.confirmedCard.classList.add('hidden');
      window.scrollTo({ top: el.serverPreviewBox.offsetTop - 50, behavior: 'smooth' });
    } catch (err) {
      showStatus(err.message || 'Failed to generate order preview.');
    } finally {
      state.isPreviewing = false;
      el.btnRequestPreview.disabled = false;
    }
  }

  // Confirm Order explicitly
  async function confirmOrder() {
    if (!state.activePreview || !state.activePreview.preview_id) {
      showStatus('No pending preview found. Please review your order first.');
      return;
    }

    hideStatus();
    state.isConfirming = true;
    el.btnConfirmOrder.disabled = true;

    try {
      const response = await fetch('/api/v1/orders/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preview_id: state.activePreview.preview_id,
          confirmed: true,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Confirmation failed with status ${response.status}`);
      }

      const orderData = await response.json();
      state.confirmedOrder = orderData;

      // Show confirmed card
      el.displayOrderId.textContent = orderData.order_id;
      el.displayOrderTime.textContent = new Date(orderData.confirmed_at).toLocaleString();
      el.displayOrderTotal.textContent = formatINR(orderData.total_inr);

      el.serverPreviewBox.classList.add('hidden');
      el.cartItemsCard.classList.add('hidden');
      el.confirmedCard.classList.remove('hidden');
      state.cart.clear();
      state.activePreview = null;
      renderCart();

      window.scrollTo({ top: el.confirmedCard.offsetTop - 50, behavior: 'smooth' });
    } catch (err) {
      showStatus(err.message || 'Order confirmation failed.');
    } finally {
      state.isConfirming = false;
      el.btnConfirmOrder.disabled = false;
    }
  }

  // Event Listeners
  function initEvents() {
    // Language toggle
    el.langSelect.addEventListener('change', (e) => {
      updateLanguage(e.target.value);
      // re-render if search results exist
      if (el.searchInput.value) {
        performSearch(
          el.searchInput.value,
          el.filterCategory.value || null,
          el.filterMaxPrice.value || null
        );
      }
      renderCart();
    });

    // Search submit
    el.searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      performSearch(
        el.searchInput.value,
        el.filterCategory.value || null,
        el.filterMaxPrice.value || null
      );
    });

    // Reset filters
    el.btnClearFilters.addEventListener('click', () => {
      el.filterCategory.value = '';
      el.filterMaxPrice.value = '';
      if (el.searchInput.value) {
        performSearch(el.searchInput.value);
      }
    });

    // Quick chip suggestion clicks
    el.chipsContainer.addEventListener('click', (e) => {
      const chip = e.target.closest('.chip');
      if (!chip) return;
      const q = chip.getAttribute('data-query');
      const max = chip.getAttribute('data-max');

      el.searchInput.value = q;
      if (max) {
        el.filterMaxPrice.value = max;
      } else {
        el.filterMaxPrice.value = '';
      }
      performSearch(q, el.filterCategory.value || null, max || null);
    });

    // Review / Preview button
    el.btnRequestPreview.addEventListener('click', requestOrderPreview);

    // Clear cart button
    el.btnClearCart.addEventListener('click', clearCart);

    // Explicit confirmation button
    el.btnConfirmOrder.addEventListener('click', confirmOrder);

    // Start another order
    el.btnNewOrder.addEventListener('click', () => {
      el.confirmedCard.classList.add('hidden');
      el.searchInput.value = '';
      el.searchInput.focus();
    });
  }

  // Initialize
  document.addEventListener('DOMContentLoaded', () => {
    initEvents();
    updateLanguage('en');
    // Pre-populate with sample initial search for immediate usability
    performSearch('glasses');
  });
})();
