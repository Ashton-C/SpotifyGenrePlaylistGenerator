const BASE = "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export interface SteamProfile {
  steamid: string;
  personaname: string;
  avatarfull: string;
  profileurl: string;
}

export interface SearchResult {
  account_id: number;
  steam64: number;
  steam_profile: SteamProfile | null;
}

export interface Match {
  match_id: number;
  hero_id: number;
  player_kills: number;
  player_deaths: number;
  player_assists: number;
  player_team: number;
  match_result: number; // winning team index; compare to player_team for win/loss
  match_duration_s: number;
  start_time: number;
  net_worth?: number;
  hero_level?: number;
  last_hits?: number;
}

export interface RankPoint {
  match_id: number;
  player_score: number; // MMR/rating value
  rank: number;
  division: number;
  division_tier: number;
  start_time: number;
}

export interface HeroStat {
  hero_id: number;
  games: number;
  wins: number;
  win_rate: number;
  avg_kills: number;
  avg_deaths: number;
  avg_assists: number;
  avg_kda: number;
}

export interface LiveMatch {
  match_id: number;
  hero_id?: number;
  duration_s?: number;
  net_worth?: number;
}

export const api = {
  search: (q: string) => get<SearchResult>(`/api/search?q=${encodeURIComponent(q)}`),
  player: (accountId: number) => get<{ account_id: number; steam64: number; steam_profile: SteamProfile | null }>(`/api/players/${accountId}`),
  matches: (accountId: number, limit = 20, offset = 0) =>
    get<Match[]>(`/api/players/${accountId}/matches?limit=${limit}&offset=${offset}`),
  rankHistory: (accountId: number) => get<RankPoint[]>(`/api/players/${accountId}/rank-history`),
  heroStats: (accountId: number) => get<HeroStat[]>(`/api/players/${accountId}/heroes`),
  liveMatch: (accountId: number) => get<LiveMatch>(`/api/players/${accountId}/live`),
};
