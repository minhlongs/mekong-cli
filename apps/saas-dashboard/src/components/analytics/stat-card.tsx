interface StatCardProps {
  title: string;
  value: string;
  change?: string;
  changeType?: 'positive' | 'negative';
}

export function StatCard({ title, value, change, changeType = 'positive' }: StatCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
        {title}
      </dt>
      <dd className="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">
        {value}
      </dd>
      {change && (
        <dd className={`mt-2 text-sm font-medium ${
          changeType === 'positive' ? 'text-green-600' : 'text-red-600'
        }`}>
          {changeType === 'positive' ? '+' : ''}{change}
        </dd>
      )}
    </div>
  );
}
