import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useState } from "react";
import "./Auth.css";

function Signup() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Google se email aayi hai kya?
  const googleEmail = searchParams.get("email") || "";
  const isGoogleSignup = searchParams.get("google") === "true";

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState(googleEmail);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      alert("Passwords do not match.");
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/auth/signup",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username,
            email,
            password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Signup failed.");
        return;
      }

     alert("Account created successfully!");

localStorage.setItem("access_token", data.access_token);
localStorage.setItem("user", JSON.stringify(data.user));

navigate("/dashboard");
    } catch (error) {
      console.error("Signup error:", error);
      alert("Unable to connect to server.");
    }
  };

  return (
    <div className="auth-page">

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

          <label htmlFor="name">
            Username
          </label>

          <input
            id="name"
            type="text"
            placeholder="Enter your username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />

          <label htmlFor="email">
            Email
          </label>

          <input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            readOnly={isGoogleSignup}
            required
          />

          <label htmlFor="password">
            Password
          </label>

          <input
            id="password"
            type="password"
            placeholder="Create a password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <label htmlFor="confirmPassword">
            Confirm Password
          </label>

          <input
            id="confirmPassword"
            type="password"
            placeholder="Confirm your password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          <button
            type="submit"
            className="auth-button"
          >
            Create Account
          </button>

        </form>

        <div className="divider">
          <span>OR</span>
        </div>

        <p className="auth-footer">
          Already have an account?{" "}
          <Link to="/login">
            Login
          </Link>
        </p>

      </div>
    </div>
  );
}

export default Signup;