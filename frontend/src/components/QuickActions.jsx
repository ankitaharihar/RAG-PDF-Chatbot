function QuickActions() {
  const actions = [
    {
      icon: "📝",
      title: "Generate Notes",
      description: "Create structured notes from your PDF.",
    },
    {
      icon: "✨",
      title: "Summarize",
      description: "Get a quick summary of your document.",
    },
    {
      icon: "🎯",
      title: "Generate MCQs",
      description: "Create practice questions from your PDF.",
    },
  ];

  return (
    <div className="features">
      {actions.map((action) => (
        <div className="feature-card" key={action.title}>
          <span>{action.icon}</span>
          <h3>{action.title}</h3>
          <p>{action.description}</p>
        </div>
      ))}
    </div>
  );
}

export default QuickActions;