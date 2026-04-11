const rows = [
  { id: "A-1001", person: "No records yet", status: "Bootstrap", time: "Waiting for API data" },
];

export default function AttendanceTable() {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Attendance</p>
          <h3>History</h3>
        </div>
        <span className="panel-tag">Placeholder data</span>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Person</th>
              <th>Status</th>
              <th>Detected</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>{row.person}</td>
                <td>{row.status}</td>
                <td>{row.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
