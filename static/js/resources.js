// ==========================================================================
// MentorAI — Curated Resources Library Handler
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  const allResources = [
    {
      title: "Binary Trees & AVL Self-Balancing Rotations",
      subject: "DSA",
      topic: "Trees",
      type: "Notes",
      source: "GeeksforGeeks",
      description: "Step-by-step breakdown of LL, RR, LR, and RL rotations with time complexity proofs and visualizations.",
      url: "https://www.geeksforgeeks.org/avl-tree-set-1-insertion/"
    },
    {
      title: "NPTEL: Database Normalization (1NF to BCNF)",
      subject: "DBMS",
      topic: "Normalization",
      type: "Video",
      source: "NPTEL",
      description: "Prof. Shamik Sural explains candidate key finding algorithm, 3NF synthesis, and lossless join testing.",
      url: "https://nptel.ac.in/courses/106105175"
    },
    {
      title: "Process Synchronization & Classic Semaphore Problems",
      subject: "Operating Systems",
      topic: "Concurrency",
      type: "Notes",
      source: "Official Documentation",
      description: "Comprehensive guide to Dining Philosophers, Producer-Consumer, and Reader-Writer synchronization with semaphores.",
      url: "https://pages.cs.wisc.edu/~remzi/OSTEP/threads-sema.pdf"
    },
    {
      title: "Dynamic Programming: 0/1 Knapsack & Subset Sum",
      subject: "DSA",
      topic: "Dynamic Programming",
      type: "Practice",
      source: "GeeksforGeeks",
      description: "Classic tabular DP problem set with recurrence relations, space optimization techniques, and edge cases.",
      url: "https://www.geeksforgeeks.org/0-1-knapsack-problem-dp-10/"
    },
    {
      title: "GATE CSE: Relational Transactions & Conflict Serializability",
      subject: "GATE CSE",
      topic: "Transactions",
      type: "PYQ",
      source: "GateOverflow",
      description: "Previous 15 years solved GATE problems on conflict equivalence, precedence graphs, and recoverability.",
      url: "https://gateoverflow.in"
    },
    {
      title: "TCP/IP vs OSI Architecture & Flow Control Mechanisms",
      subject: "Computer Networks",
      topic: "Transport Layer",
      type: "Notes",
      source: "GeeksforGeeks",
      description: "Deep dive into Stop-and-Wait, Go-Back-N, and Selective Repeat ARQ window calculations and throughput equations.",
      url: "https://www.geeksforgeeks.org/sliding-window-protocol-set-1/"
    },
    {
      title: "Virtual Memory, Paging & Belady's Anomaly",
      subject: "Operating Systems",
      topic: "Memory Management",
      type: "Video",
      source: "NPTEL",
      description: "Lecture on hierarchical page tables, TLB hits/misses, and FIFO vs LRU page replacement trade-offs.",
      url: "https://nptel.ac.in/courses/106106144"
    },
    {
      title: "Java Collections Framework: HashMap Deep Dive",
      subject: "Java",
      topic: "Collections",
      type: "Notes",
      source: "Official Documentation",
      description: "Explains array bucket resizing, hashCode distribution, equals contracts, and Java 8 treeify conversions.",
      url: "https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/HashMap.html"
    },
    {
      title: "SQL Window Functions & Subqueries Mastery",
      subject: "Java",
      topic: "SQL",
      type: "Practice",
      source: "MDN",
      description: "Hands-on drills for DENSE_RANK, ROW_NUMBER, OVER (PARTITION BY), and correlated subqueries.",
      url: "https://developer.mozilla.org"
    },
    {
      title: "Graph Algorithms: Dijkstra & Bellman-Ford Shortest Paths",
      subject: "DSA",
      topic: "Graphs",
      type: "Practice",
      source: "GeeksforGeeks",
      description: "Greedy single-source shortest path implementation with priority queues, plus handling negative edge weights.",
      url: "https://www.geeksforgeeks.org/dijkstras-shortest-path-algorithm-greedy-algo-7/"
    },
    {
      title: "Deadlocks: Banker's Safety Algorithm & Resource Request",
      subject: "Operating Systems",
      topic: "Deadlocks",
      type: "PYQ",
      source: "GateOverflow",
      description: "Step-by-step verification of safe sequences and deadlock avoidance in multi-instance resource systems.",
      url: "https://gateoverflow.in"
    },
    {
      title: "B+ Trees Indexing & Disk Block Access Optimization",
      subject: "DBMS",
      topic: "Indexing",
      type: "Notes",
      source: "Official Documentation",
      description: "Mathematical derivation of B+ Tree order, fan-out, root-to-leaf depth, and range search I/O savings.",
      url: "https://pages.cs.wisc.edu/~dbbook/"
    },
    {
      title: "Subnetting, CIDR Notation & IP Addressing Drills",
      subject: "Computer Networks",
      topic: "Network Layer",
      type: "Practice",
      source: "GeeksforGeeks",
      description: "Practice problems for calculating network masks, broadcast addresses, and routing table longest-prefix matches.",
      url: "https://www.geeksforgeeks.org/ip-addressing-and-subnetting/"
    },
    {
      title: "GATE CSE: Discrete Mathematics & Propositional Logic",
      subject: "GATE CSE",
      topic: "Discrete Math",
      type: "PYQ",
      source: "GateOverflow",
      description: "Tautologies, predicate logic quantifiers, set relations, posets, and lattice problems from GATE archives.",
      url: "https://gateoverflow.in"
    }
  ];

  let currentFilter = 'all';
  let searchQuery = '';
  let displayCount = 9; // Limit initial display to 9

  const grid = document.getElementById('resourcesGrid');
  const searchInput = document.getElementById('resourceSearchInput');
  const loadMoreBtn = document.getElementById('loadMoreBtn');
  const filterChips = document.querySelectorAll('.filter-chip');

  // Filter chips click handling
  filterChips.forEach(chip => {
    chip.addEventListener('click', () => {
      filterChips.forEach(c => {
        c.classList.remove('btn-primary', 'active');
        c.classList.add('btn-secondary');
      });
      chip.classList.remove('btn-secondary');
      chip.classList.add('btn-primary', 'active');

      currentFilter = chip.dataset.filter;
      displayCount = 9;
      renderResources();
    });
  });

  // Search input handler
  searchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value.toLowerCase().trim();
    displayCount = 9;
    renderResources();
  });

  // Load More button
  loadMoreBtn.addEventListener('click', () => {
    displayCount += 6;
    renderResources();
  });

  function renderResources() {
    grid.innerHTML = '';

    const filtered = allResources.filter(item => {
      const matchesFilter = (currentFilter === 'all') || (item.subject.toLowerCase() === currentFilter.toLowerCase());
      const matchesSearch = !searchQuery ||
        item.title.toLowerCase().includes(searchQuery) ||
        item.topic.toLowerCase().includes(searchQuery) ||
        item.source.toLowerCase().includes(searchQuery) ||
        item.description.toLowerCase().includes(searchQuery);

      return matchesFilter && matchesSearch;
    });

    if (filtered.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 1rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔍</div>
          <h3 style="color: #fff; margin-bottom: 0.5rem;">No resources found</h3>
          <p style="color: var(--text-muted); font-size: 0.95rem;">Try another keyword or select "All Resources".</p>
        </div>
      `;
      loadMoreBtn.style.display = 'none';
      return;
    }

    const visibleItems = filtered.slice(0, displayCount);

    visibleItems.forEach(item => {
      const card = document.createElement('div');
      card.className = 'glass-card card-hover-lift';
      card.style.display = 'flex';
      card.style.flexDirection = 'column';
      card.style.justifyContent = 'space-between';

      const typeBadgeClass = item.type === 'Video' ? 'badge-cyan' : (item.type === 'Practice' ? 'badge-success' : (item.type === 'PYQ' ? 'badge-warning' : 'badge-primary'));

      card.innerHTML = `
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <span class="badge badge-primary">${item.subject}</span>
            <div style="display: flex; gap: 0.35rem;">
              <span class="badge ${typeBadgeClass}">${item.type}</span>
              <span class="badge badge-cyan" style="font-size: 0.7rem;">${item.source}</span>
            </div>
          </div>

          <h3 style="font-size: 1.12rem; color: #fff; margin-bottom: 0.5rem; line-height: 1.4;">
            ${item.title}
          </h3>

          <p style="color: var(--text-muted); font-size: 0.88rem; line-height: 1.55; margin-bottom: 1.25rem;">
            ${item.description}
          </p>
        </div>

        <div>
          <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm btn-block" style="font-size: 0.82rem;">
            Open Resource ↗
          </a>
        </div>
      `;

      grid.appendChild(card);
    });

    // Hide or show Load More button
    if (displayCount >= filtered.length) {
      loadMoreBtn.style.display = 'none';
    } else {
      loadMoreBtn.style.display = 'inline-flex';
    }
  }

  // Initial render
  renderResources();
});
