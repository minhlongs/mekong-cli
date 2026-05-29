import { getDepartments } from "@/lib/department-config";
import DepartmentPage from "./department-page";

export function generateStaticParams() {
  const depts = getDepartments();
  return depts.map((d) => ({
    department: d.slug,
  }));
}

export default function Page() {
  return <DepartmentPage />;
}
