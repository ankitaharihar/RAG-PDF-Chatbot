import QuickActions from "./QuickActions";

function ChatArea() {
  return (
    <main className="chat-area">
      <div className="welcome">
        <div className="welcome-icon">🤖</div>

        <h2>What would you like to learn?</h2>

        <p>
          Upload a PDF and ask questions, generate notes,
          summaries, or practice questions.
        </p>

        <QuickActions />
      </div>
    </main>
  );
}

export default ChatArea;