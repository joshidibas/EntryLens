export default function EnrollmentForm() {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Enrollment</p>
          <h3>Add Identity</h3>
        </div>
        <span className="panel-tag">Scaffold</span>
      </div>

      <form className="enroll-form">
        <label>
          Full name
          <input type="text" placeholder="Avery Johnson" disabled />
        </label>
        <label>
          Role
          <select disabled defaultValue="staff">
            <option value="staff">Staff</option>
            <option value="visitor">Visitor</option>
          </select>
        </label>
        <label>
          Sample images
          <input type="file" multiple disabled />
        </label>
        <button type="button" disabled>
          Enrollment flow arrives in the next milestone
        </button>
      </form>
    </section>
  );
}
