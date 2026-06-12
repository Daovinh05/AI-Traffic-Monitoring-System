import { LegacyFrame } from "@/components/LegacyFrame";

type UserHistoryPageProps = {
  searchParams: Promise<{ tab?: string }>;
};

export default async function UserHistoryPage({
  searchParams,
}: UserHistoryPageProps) {
  const { tab } = await searchParams;
  const path = tab === "warnings" ? "/lich_su?tab=warnings" : "/lich_su";

  return <LegacyFrame title="AI Traffic Monitoring History" path={path} />;
}
