import { JobStatus } from "@english-channel/shared-types";

export default function HomePage() {
  return (
    <main>
      <h1>English Channel Control Panel</h1>
      <section className="card">
        <h2>Default Job Statuses</h2>
        <ul>
          {Object.values(JobStatus).map((status) => (
            <li key={status}>{status}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
