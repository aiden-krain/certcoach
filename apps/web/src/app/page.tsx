export default function Home() {
  return (
    <main className="container mx-auto px-4 py-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-6">
          Welcome to CertCoach
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Master technical certifications with AI-powered study planning and adaptive practice
        </p>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-4xl mx-auto">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Blueprint-first Planning</h3>
            <p className="text-gray-600">
              Study plans based on official exam weights with automatic rescheduling
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Adaptive Practice</h3>
            <p className="text-gray-600">
              AI-powered sessions with rationales and official documentation links
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Mastery Tracking</h3>
            <p className="text-gray-600">
              Per-objective probability tracking with weekly gap analysis
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Smart Flashcards</h3>
            <p className="text-gray-600">
              One-click spaced repetition from your own study notes
            </p>
          </div>
        </div>
        <div className="mt-8">
          <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg">
            Start Your Study Plan
          </button>
        </div>
      </div>
    </main>
  )
}
