import { useEffect, useState } from 'react'

interface Props {
  message: string | null
  duration?: number
}

export default function InfoBanner({ message, duration = 2000 }: Props) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (!message) { setVisible(false); return }
    setVisible(true)
    const t = setTimeout(() => setVisible(false), duration)
    return () => clearTimeout(t)
  }, [message, duration])

  if (!visible) return null
  return (
    <div className="max-w-4xl mx-auto mb-4 p-3 bg-green-100 text-green-700 rounded border border-green-300">
      {message}
    </div>
  )
}
