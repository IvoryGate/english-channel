import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';

export type EnglishListeningRoomShortThumbnailProps = {
  format: 'micro_story' | 'listen_choose' | 'dialogue' | 'classic_cliffhanger';
  cefr: 'A2' | 'B1';
  headline: string;
  backgroundImage: string;
  brandLogo: string;
};

const palettes = {
  micro_story: {accent: '#B85F5A', label: 'A TINY ENGLISH STORY'},
  listen_choose: {accent: '#647A72', label: 'LISTEN & CHOOSE'},
  dialogue: {accent: '#9B6285', label: 'REAL-LIFE ENGLISH'},
  classic_cliffhanger: {accent: '#9B7243', label: 'CLASSIC CLIFFHANGER'},
} as const;

export const EnglishListeningRoomShortThumbnail: React.FC<
  EnglishListeningRoomShortThumbnailProps
> = ({format, cefr, headline, backgroundImage, brandLogo}) => {
  const palette = palettes[format];
  return (
    <AbsoluteFill style={{backgroundColor: '#3D2B24', fontFamily: 'Inter, Arial, sans-serif'}}>
      <Img
        src={staticFile(backgroundImage)}
        style={{height: '100%', objectFit: 'cover', width: '100%'}}
      />
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(35,22,18,0.12) 0%, rgba(35,22,18,0.01) 38%, rgba(35,22,18,0.52) 76%, rgba(35,22,18,0.76) 100%)',
        }}
      />
      <div
        style={{
          alignItems: 'center',
          display: 'flex',
          gap: 22,
          left: 46,
          position: 'absolute',
          right: 46,
          top: 42,
        }}
      >
        <div
          style={{
            backgroundColor: '#FFF9F0',
            border: '3px solid rgba(255,255,255,0.86)',
            borderRadius: 999,
            boxShadow: '0 8px 24px rgba(42,25,18,0.28)',
            height: 124,
            overflow: 'hidden',
            width: 124,
          }}
        >
          <Img
            src={staticFile(brandLogo)}
            style={{height: '100%', objectFit: 'cover', width: '100%'}}
          />
        </div>
        <div style={{color: '#FFF9F0', textShadow: '0 3px 18px rgba(34,20,14,0.7)'}}>
          <div style={{fontFamily: 'Georgia, serif', fontSize: 40, fontWeight: 700}}>
            English Listening Room
          </div>
          <div style={{fontSize: 24, fontWeight: 780, letterSpacing: 1.5, marginTop: 4}}>
            LISTEN • UNDERSTAND • GROW
          </div>
        </div>
      </div>
      <div style={{bottom: 96, left: 54, position: 'absolute', right: 54}}>
        <div
          style={{
            alignItems: 'center',
            display: 'flex',
            gap: 20,
            marginBottom: 20,
          }}
        >
          <div
            style={{
              backgroundColor: palette.accent,
              borderRadius: 999,
              color: '#FFF9F0',
              fontSize: 30,
              fontWeight: 850,
              letterSpacing: 1.3,
              padding: '14px 26px',
            }}
          >
            {palette.label}
          </div>
          <div
            style={{
              backgroundColor: 'rgba(255,249,240,0.94)',
              borderRadius: 999,
              color: palette.accent,
              fontSize: 30,
              fontWeight: 900,
              padding: '14px 22px',
            }}
          >
            {cefr}
          </div>
        </div>
        <div
          style={{
            color: '#FFF9F0',
            fontFamily: 'Georgia, Times New Roman, serif',
            fontSize: headline.length > 25 ? 88 : 102,
            fontWeight: 750,
            letterSpacing: -2.4,
            lineHeight: 1.02,
            maxWidth: 930,
            textShadow: '0 10px 32px rgba(25,14,10,0.76)',
          }}
        >
          {headline}
        </div>
        <div
          style={{
            backgroundColor: palette.accent,
            borderRadius: 999,
            height: 12,
            marginTop: 28,
            width: 170,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
