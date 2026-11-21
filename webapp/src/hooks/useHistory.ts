import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { HistoryItem, HistoryPage, Platform } from "../api/types";

const PAGE_SIZE = 20;

export function useHistory(platform: Platform | "all", query: string) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [counts, setCounts] = useState<HistoryPage["counts"]>({
    all: 0,
    instagram: 0,
    tiktok: 0,
    youtube: 0,
    facebook: 0,
  });
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  const load = useCallback(
    async (nextPage: number, replace: boolean) => {
      setStatus("loading");
      if (replace) setItems([]);
      try {
        const result = await api.getHistory({ platform, query, page: nextPage, pageSize: PAGE_SIZE });
        setItems((current) => (replace ? result.items : [...current, ...result.items]));
        setTotal(result.total);
        setCounts(result.counts);
        setPage(nextPage);
        setStatus("ready");
      } catch (error) {
        if (error instanceof ApiError) setStatus("error");
        else setStatus("error");
      }
    },
    [platform, query],
  );

  useEffect(() => {
    void load(1, true);
  }, [load]);

  return {
    items,
    counts,
    status,
    hasMore: items.length < total,
    reload: () => load(1, true),
    loadMore: () => load(page + 1, false),
    remove(id: string) {
      setItems((current) => current.filter((item) => item.id !== id));
      setTotal((value) => Math.max(0, value - 1));
      setCounts((current) => {
        const found = items.find((item) => item.id === id);
        if (!found) return current;
        return {
          ...current,
          all: Math.max(0, current.all - 1),
          [found.platform]: Math.max(0, current[found.platform] - 1),
        };
      });
    },
  };
}
