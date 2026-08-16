import { useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Auth.css";

function Login() {
  const navigate = useNavigate();
  const googleButtonRef = useRef(null);

useEffect(() => {
  const script = document.createElement("script");
  script.src = "https://accounts.google.com/gsi/client";
  script.async = true;
  script.defer = true;

  script.onload = () => {
    if (!window.google || !googleButtonRef.current) return;

    window.google.accounts.id.initialize({
      client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,

     callback: async (response) => {
  try {
    const res = await fetch("http://127.0.0.1:8000/api/auth/google", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        credential: response.credential,
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      console.error("Google login failed:", data);
      alert(data.detail || "Google login failed");
      return;
    }

    console.log("Google login successful:", data);

    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));

    navigate("/dashboard");
  } catch (error) {
    console.error("Google login error:", error);
    alert("Unable to connect to server.");
  }
},
    });

    window.google.accounts.id.renderButton(
      googleButtonRef.current,
      {
        theme: "outline",
        size: "large",
        width: 360,
        text: "signin_with",
      }
    );
  };

  document.body.appendChild(script);

  return () => {
    document.body.removeChild(script);
  };
}, []);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const email = e.target.email.value.trim();
    const password = e.target.password.value;

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/auth/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Login failed.");
        return;
      }

      // Save authentication data
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));

      // Go to dashboard
      navigate("/dashboard");
    } catch (error) {
      console.error("Login error:", error);
      alert("Unable to connect to the server.");
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

        <h1>Welcome back</h1>

        <p className="auth-subtitle">
          Login to continue learning with PDF AI
        </p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="email">Email</label>

          <input
            id="email"
            name="email"
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
            name="password"
            type="password"
            placeholder="Enter your password"
            required
          />

          <button type="submit" className="auth-button">
            Login
          </button>
        </form>
<div
  ref={googleButtonRef}
  className="google-login-button"
></div>
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