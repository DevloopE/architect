import { Agentation } from 'agentation'
import { GeistPixelSquare } from 'geist/font/pixel'
import { Barlow } from 'next/font/google'
import localFont from 'next/font/local'
import Script from 'next/script'
import './globals.css'

const geistSans = localFont({
  src: './fonts/GeistVF.woff',
  variable: '--font-geist-sans',
})
const geistMono = localFont({
  src: './fonts/GeistMonoVF.woff',
  variable: '--font-geist-mono',
})

const barlow = Barlow({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-barlow',
  display: 'swap',
})

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      className={`${geistSans.variable} ${geistMono.variable} ${GeistPixelSquare.variable} ${barlow.variable}`}
      lang="en"
    >
      <head>
        <style>{`
          nextjs-portal { display: none !important; }
          [data-nextjs-dialog-overlay] { display: none !important; }
          [data-nextjs-toast] { display: none !important; }
          #__next-build-indicator { display: none !important; }
          [data-nextjs-scroll] { display: none !important; }
        `}</style>
      </head>
      <body className="font-sans">
        {children}
      </body>
    </html>
  )
}
