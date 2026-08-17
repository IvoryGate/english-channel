import React from 'react';
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export type ShortScene = {
  speaker: string;
  text: string;
  startSec: number;
  endSec: number;
};

export type EnglishListeningRoomShortProps = {
  shortId: string;
  format: 'micro_story' | 'listen_choose' | 'dialogue' | 'classic_cliffhanger';
  cefr: 'A2' | 'B1';
  durationSec: number;
  hook: string;
  hookEndSec: number;
  scenes: ShortScene[];
  prompt: string;
  answer: string;
  promptStartSec: number;
  answerStartSec: number;
};

const palettes = {
  micro_story: {top: '#103E48', bottom: '#071E26', accent: '#FFCF66', soft: '#D6F4F1'},
  listen_choose: {top: '#253B76', bottom: '#101A3C', accent: '#FFD166', soft: '#E9EEFF'},
  dialogue: {top: '#5A315B', bottom: '#25172E', accent: '#7EE0D6', soft: '#F7E9FA'},
  classic_cliffhanger: {top: '#49351F', bottom: '#1F180F', accent: '#E8C98D', soft: '#FFF4DD'},
} as const;

const formatLabels = {
  micro_story: 'MICRO STORY',
  listen_choose: 'LISTEN & CHOOSE',
  dialogue: 'REAL ENGLISH',
  classic_cliffhanger: 'CLASSIC CLIFFHANGER',
} as const;

const SpeakerChip: React.FC<{speaker: string; accent: string}> = ({speaker, accent}) => {
  if (speaker === 'narrator') {
    return null;
  }
  return (
    <div
      style={{
        alignSelf: speaker === 'riley' ? 'flex-start' : 'flex-end',
        backgroundColor: accent,
        borderRadius: 999,
        color: '#10232B',
        fontSize: 30,
        fontWeight: 800,
        letterSpacing: 1.5,
        marginBottom: 22,
        padding: '10px 24px',
        textTransform: 'uppercase',
      }}
    >
      {speaker}
    </div>
  );
};

export const EnglishListeningRoomShort: React.FC<EnglishListeningRoomShortProps> = (props) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const second = frame / fps;
  const palette = palettes[props.format];
  const activeScene =
    props.scenes.find((scene) => second >= scene.startSec && second < scene.endSec) ??
    props.scenes[props.scenes.length - 1];
  const hookActive = second < props.hookEndSec;
  const promptActive = second >= props.promptStartSec && second < props.answerStartSec;
  const answerActive = second >= props.answerStartSec;
  const sceneStartFrame = activeScene ? Math.round(activeScene.startSec * fps) : 0;
  const entrance = spring({
    fps,
    frame: Math.max(0, frame - sceneStartFrame),
    config: {damping: 16, stiffness: 150, mass: 0.8},
  });
  const hookScale = interpolate(frame, [0, 12], [0.94, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const progress = `${Math.max(0, Math.min(100, (frame / durationInFrames) * 100))}%`;
  const mainText = hookActive
    ? props.hook
    : answerActive
      ? props.answer
      : promptActive
        ? props.prompt
        : activeScene?.text ?? props.hook;
  const eyebrow = hookActive
    ? 'LISTEN CLOSELY'
    : answerActive
      ? 'ANSWER'
      : promptActive
        ? 'YOUR TURN'
        : activeScene?.speaker === 'narrator'
          ? 'KEEP LISTENING'
          : 'CONVERSATION';

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(160deg, ${palette.top} 0%, ${palette.bottom} 75%)`,
        color: '#FFFFFF',
        fontFamily: 'Inter, Manrope, Arial, sans-serif',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          background: `radial-gradient(circle, ${palette.accent}33 0%, transparent 68%)`,
          height: 900,
          opacity: 0.85,
          position: 'absolute',
          right: -340,
          top: -250,
          width: 900,
        }}
      />
      <div
        style={{
          border: `2px solid ${palette.accent}2B`,
          borderRadius: 72,
          bottom: 230,
          left: -220,
          position: 'absolute',
          transform: 'rotate(18deg)',
          width: 720,
          height: 720,
        }}
      />

      <div style={{display: 'flex', justifyContent: 'space-between', padding: '78px 64px 0'}}>
        <div
          style={{
            border: `2px solid ${palette.accent}`,
            borderRadius: 999,
            color: palette.accent,
            fontSize: 27,
            fontWeight: 900,
            letterSpacing: 2.4,
            padding: '12px 24px',
          }}
        >
          {formatLabels[props.format]}
        </div>
        <div style={{color: palette.soft, fontSize: 30, fontWeight: 900}}>{props.cefr}</div>
      </div>

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          left: 74,
          minHeight: 920,
          position: 'absolute',
          right: 74,
          top: 300,
        }}
      >
        {!hookActive && !promptActive && !answerActive && activeScene ? (
          <SpeakerChip speaker={activeScene.speaker} accent={palette.accent} />
        ) : null}
        <div
          style={{
            color: answerActive ? palette.accent : palette.soft,
            fontSize: 27,
            fontWeight: 900,
            letterSpacing: 3.2,
            marginBottom: 34,
          }}
        >
          {eyebrow}
        </div>
        <div
          style={{
            fontSize: hookActive || promptActive ? 76 : answerActive ? 70 : 66,
            fontWeight: 850,
            letterSpacing: -2.2,
            lineHeight: 1.16,
            opacity: hookActive ? 1 : entrance,
            textShadow: '0 8px 30px rgba(0,0,0,0.28)',
            transform: hookActive
              ? `scale(${hookScale})`
              : `translateY(${interpolate(entrance, [0, 1], [28, 0])}px)`,
          }}
        >
          {mainText}
        </div>
        {promptActive ? (
          <div
            style={{
              color: palette.accent,
              fontSize: 30,
              fontWeight: 750,
              letterSpacing: 1.2,
              marginTop: 46,
            }}
          >
            Pause. Say your answer out loud.
          </div>
        ) : null}
      </div>

      <div style={{bottom: 118, left: 64, position: 'absolute', right: 64}}>
        <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 24}}>
          <div style={{fontSize: 29, fontWeight: 850, letterSpacing: 0.5}}>English Listening Room</div>
          <div style={{color: palette.soft, fontSize: 24, fontWeight: 700}}>{props.shortId}</div>
        </div>
        <div style={{backgroundColor: '#FFFFFF24', borderRadius: 999, height: 8, overflow: 'hidden'}}>
          <div style={{backgroundColor: palette.accent, borderRadius: 999, height: '100%', width: progress}} />
        </div>
      </div>
    </AbsoluteFill>
  );
};
