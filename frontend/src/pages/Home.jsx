import { Link } from "react-router-dom";
import "./Home.css";

function Home() {
  return (
    <div className="home-page">

      {/* Navbar */}
      <nav className="navbar">
        <Link to="/" className="brand">
          <span className="brand-icon">📚</span>
          <span>PDF AI</span>
        </Link>

        <div className="nav-links">
          <a href="#features">Features</a>
          <Link to="/login">Log in</Link>
          <Link to="/signup" className="nav-signup">
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <main className="hero">

        <div className="hero-badge">
          ✨ AI-powered PDF learning assistant
        </div>

        <h1>
          Turn your PDFs into
          <span> an AI study assistant.</span>
        </h1>

        <p>
          Upload your documents, ask questions, generate summaries,
          create notes, and prepare for exams or interviews.
        </p>

        <div className="hero-buttons">
          <Link to="/signup" className="primary-btn">
            Start Learning →
          </Link>

          <a href="#features" className="secondary-btn">
            Explore Features
          </a>
        </div>

        <div className="hero-preview">
          <div className="preview-top">
            <span>📄 Research_Paper.pdf</span>
            <span className="ready">● Ready</span>
          </div>

          <div className="preview-content">
            <div className="ai-avatar">🤖</div>

            <p className="question">
              What are the main findings of this paper?
            </p>

            <div className="answer">
              <strong>AI Answer</strong>
              <p>
                The document highlights improvements in efficiency,
                accuracy, and practical implementation.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Features */}
      <section id="features" className="features-section">

        <div className="section-heading">
          <span>POWERFUL FEATURES</span>
          <h2>Everything you need to study smarter.</h2>
          <p>
            One workspace for understanding, revising and learning
            from your documents.
          </p>
        </div>

        <div className="feature-grid">

          <div className="feature-card">
            <div className="feature-icon">💬</div>
            <h3>Chat with PDFs</h3>
            <p>
              Ask questions and get answers directly from your documents.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">✨</div>
            <h3>Smart Summaries</h3>
            <p>
              Quickly understand long documents with AI-generated summaries.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">📝</div>
            <h3>Generate Notes</h3>
            <p>
              Turn your PDFs into structured study notes.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3>Generate MCQs</h3>
            <p>
              Create practice questions from your study material.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🎤</div>
            <h3>Interview Prep</h3>
            <p>
              Generate interview questions based on your documents.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">📚</div>
            <h3>PDF Library</h3>
            <p>
              Keep all your learning documents organized in one place.
            </p>
          </div>

        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <h2>Ready to learn smarter?</h2>
        <p>Upload your first PDF and start asking questions.</p>

        <Link to="/signup" className="primary-btn">
          Create Free Account →
        </Link>
      </section>

      <footer>
        <div className="brand">
          <span className="brand-icon">📚</span>
          PDF AI
        </div>
        <p>AI-powered learning from your documents.</p>
      </footer>

    </div>
  );
}

export default Home;