import { Link, useNavigate } from "react-router-dom";
import "./Auth.css";

function Login() {
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

        <h1>Welcome back</h1>

        <p className="auth-subtitle">
          Login to continue learning with PDF AI
        </p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="email">Email</label>

          <input
            id="email"
            type="email"
            placeholder="you@example.com"
            required
          />

          <div className="password-row">
            <label htmlFor="password">Password</label>

            <Link to="/forgot-password">
              Forgot password?
            </Link>
          </div>

          <input
            id="password"
            type="password"
            placeholder="Enter your password"
            required
          />

          <button type="submit" className="auth-button">
            Login
          </button>
        </form>

        <div className="divider">
          <span>OR</span>
        </div>

        <p className="auth-footer">
          Don't have an account?{" "}
          <Link to="/signup">Create an account</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;