/** Client-only .xlsx export — dynamically imports `xlsx` so it never lands in the SSR bundle. */
export async function exportToExcel(
  filename: string,
  sheetName: string,
  rows: Record<string, string | number>[],
) {
  const XLSX = await import("xlsx");
  const worksheet = XLSX.utils.json_to_sheet(rows);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
  XLSX.writeFile(workbook, filename.endsWith(".xlsx") ? filename : `${filename}.xlsx`);
}

/**
 * Walks every page of a paginated admin list endpoint and returns the full
 * (filtered) result set — export buttons must cover all matching rows, not
 * just the page currently on screen.
 */
export async function fetchAllPages<T>(
  fetchPage: (page: number, pageSize: number) => Promise<{ items: T[]; total: number }>,
  pageSize: number,
): Promise<T[]> {
  const first = await fetchPage(1, pageSize);
  const all = [...first.items];
  const totalPages = Math.ceil(first.total / pageSize);
  for (let page = 2; page <= totalPages; page++) {
    const next = await fetchPage(page, pageSize);
    all.push(...next.items);
  }
  return all;
}
