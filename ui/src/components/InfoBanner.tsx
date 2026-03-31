import { useEffect, useState } from 'react'

interface Props {
  message: string | null
  duration?: number
}

function InfoBannerInner({ message, duration = 2000 }: { message: string; duration?: number }) {
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const t = setTimeout(() => setVisible(false), duration)
    return () => clearTimeout(t)
  }, [duration])

  if (!visible) return null
  return (
    <div className="max-w-4xl mx-auto mb-4 p-3 bg-green-100 text-green-700 rounded border border-green-300">
      {message}
    </div>
  )
}

export default function InfoBanner({ message, duration }: Props) {
  if (!message) return null
  return <InfoBannerInner key={message} message={message} duration={duration} />
}
