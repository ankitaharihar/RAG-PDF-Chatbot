import { Link, useNavigate } from "react-router-dom";

function Signup() {
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();

    // Abhi frontend demo navigation
    navigate("/dashboard");
  };

  return (
    <div className="auth-page">
      {/* Brand */}
      <Link to="/" className="auth-brand brand">
        <span className="brand-icon">📚</span>
        <span>PDF AI</span>
      </Link>

      <div className="auth-card">
        <div className="auth-icon">📚</div>

        <h1>Create your account</h1>

        <p className="auth-subtitle">
          Start learning smarter with PDF AI
        </p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="name">Full Name</label>

          <input
            id="name"
            type="text"
            placeholder="Enter your name"
            required
          />

          <label htmlFor="email">Email</label>

          <input
            id="email"
            type="email"
            placeholder="you@example.com"
            required
          />

          <label htmlFor="password">Password</label>

          <input
            id="password"
            type="password"
            placeholder="Create a password"
            required
          />

          <label htmlFor="confirmPassword">
            Confirm Password
          </label>

          <input
            id="confirmPassword"
            type="password"
            placeholder="Confirm your password"
            required
          />

          <button type="submit" className="auth-button">
            Create Account
          </button>
        </form>

        <div className="divider">
          <span>OR</span>
        </div>

        <p className="auth-footer">
          Already have an account?{" "}
          <Link to="/login">Login</Link>
        </p>
      </div>
    </div>
  );
}

export default Signup;