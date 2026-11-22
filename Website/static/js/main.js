// Currency formatter used by the chart axis callbacks in the templates.
window.gbp = function (value) {
  return "£" + Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 });
};

document.addEventListener("DOMContentLoaded", () => {
  // 1) Live search: <input data-search-target="tableId"> filters that table's rows.
  document.querySelectorAll("input[data-search-target]").forEach((input) => {
    const table = document.getElementById(input.dataset.searchTarget);
    if (!table) return;
    input.addEventListener("input", () => {
      const q = input.value.trim().toLowerCase();
      table.querySelectorAll("tbody tr").forEach((tr) => {
        tr.style.display = tr.textContent.toLowerCase().includes(q) ? "" : "none";
      });
    });
  });

  // 2) Click a header in a .sortable table to sort by that column.
  //    Cells can carry data-value="<raw number>" so currency sorts numerically.
  document.querySelectorAll("table.sortable").forEach((table) => {
    const tbody = table.tBodies[0];
    table.querySelectorAll("thead th").forEach((th, colIndex) => {
      th.addEventListener("click", () => {
        const asc = th.dataset.asc !== "true";
        table.querySelectorAll("thead th").forEach((h) => delete h.dataset.asc);
        th.dataset.asc = String(asc);

        const rows = Array.from(tbody.rows);
        rows.sort((a, b) => {
          const x = a.cells[colIndex]?.dataset.value ?? a.cells[colIndex]?.textContent.trim() ?? "";
          const y = b.cells[colIndex]?.dataset.value ?? b.cells[colIndex]?.textContent.trim() ?? "";
          const nx = parseFloat(x), ny = parseFloat(y);
          const cmp = !isNaN(nx) && !isNaN(ny) ? nx - ny : String(x).localeCompare(String(y));
          return asc ? cmp : -cmp;
        });
        rows.forEach((r) => tbody.appendChild(r));
      });
    });
  });
});
