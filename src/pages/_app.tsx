import React from 'react';
import { AppProps } from 'next/app';
import '../styles/globals.css';
import { Toaster } from '@/components/ui/toast/toaster';

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <>
      <Component {...pageProps} />
      <Toaster />
    </>
  );
}

export default MyApp;
