interface Props {
  message: string | null
}

export default function ErrorBanner({ message }: Props) {
  if (!message) return null
  return (
    <div className="max-w-4xl mx-auto mb-4 p-3 bg-red-100 text-red-700 rounded border border-red-300">
      {message}
    </div>
  )
}
