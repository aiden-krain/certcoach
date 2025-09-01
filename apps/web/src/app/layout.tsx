import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'CertCoach - Adaptive Exam Preparation',
  description: 'Master technical certifications with AI-powered study planning and spaced repetition',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <div id="root">
          {children}
        </div>
      </body>
    </html>
  )
}
