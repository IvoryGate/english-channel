import React from 'react';
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  spring,
  staticFile,
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
  backgroundImage: string;
  brandLogo: string;
  cta: string;
};

const palettes = {
  micro_story: {accent: '#B85F5A', ink: '#39251D', paper: '#FFF8EF'},
  listen_choose: {accent: '#647A72', ink: '#28332F', paper: '#F7FAF5'},
  dialogue: {accent: '#9B6285', ink: '#392735', paper: '#FFF7FC'},
  classic_cliffhanger: {accent: '#9B7243', ink: '#34291F', paper: '#FFF9ED'},
} as const;

const formatLabels = {
  micro_story: 'A tiny English story',
  listen_choose: 'Listen & choose',
  dialogue: 'Real-life English',
  classic_cliffhanger: 'Classic cliffhanger',
} as const;

const SpeakerChip: React.FC<{speaker: string; accent: string}> = ({speaker, accent}) => {
  if (speaker === 'narrator') {
    return null;
  }
  return (
    <div
      style={{
        alignSelf: speaker === 'riley' ? 'flex-start' : 'flex-end',
        backgroundColor: `${accent}1F`,
        border: `2px solid ${accent}55`,
        borderRadius: 999,
        color: accent,
        fontFamily: 'Inter, Arial, sans-serif',
        fontSize: 27,
        fontWeight: 800,
        marginBottom: 20,
        padding: '9px 22px',
        textTransform: 'capitalize',
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
  const ctaActive = second >= props.durationSec - 3.5;
  const sceneStartFrame = activeScene ? Math.round(activeScene.startSec * fps) : 0;
  const entrance = spring({
    fps,
    frame: Math.max(0, frame - sceneStartFrame),
    config: {damping: 18, stiffness: 135, mass: 0.85},
  });
  const hookScale = interpolate(frame, [0, 14], [0.96, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const backgroundScale = interpolate(frame, [0, durationInFrames], [1.04, 1.12], {
    extrapolateRight: 'clamp',
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
    ? 'Listen closely'
    : answerActive
      ? 'The answer'
      : promptActive
        ? 'Your turn'
        : activeScene?.speaker === 'narrator'
          ? 'Keep listening'
          : 'Conversation';

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#4A352C',
        color: palette.ink,
        fontFamily: 'Inter, Arial, sans-serif',
        overflow: 'hidden',
      }}
    >
      <Img
        src={staticFile(props.backgroundImage)}
        style={{
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${backgroundScale}) translateX(-1.2%)`,
          width: '100%',
        }}
      />
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(45,30,24,0.58) 0%, rgba(45,30,24,0.04) 25%, rgba(45,30,24,0.12) 62%, rgba(45,30,24,0.72) 100%)',
        }}
      />

      <div
        style={{
          alignItems: 'center',
          display: 'flex',
          justifyContent: 'space-between',
          left: 54,
          position: 'absolute',
          right: 54,
          top: 58,
        }}
      >
        <div style={{alignItems: 'center', display: 'flex', gap: 18}}>
          <div
            style={{
              backgroundColor: '#FFF9F0',
              border: '3px solid rgba(255,255,255,0.82)',
              borderRadius: 999,
              boxShadow: '0 8px 24px rgba(42,25,18,0.25)',
              height: 88,
              overflow: 'hidden',
              width: 88,
            }}
          >
            <Img
              src={staticFile(props.brandLogo)}
              style={{height: '100%', objectFit: 'cover', width: '100%'}}
            />
          </div>
          <div style={{color: '#FFF9F0', textShadow: '0 3px 18px rgba(34,20,14,0.55)'}}>
            <div style={{fontFamily: 'Georgia, serif', fontSize: 31, fontWeight: 700}}>
              English Listening Room
            </div>
            <div style={{fontSize: 20, fontWeight: 650, letterSpacing: 1.4, marginTop: 3}}>
              LISTEN • UNDERSTAND • GROW
            </div>
          </div>
        </div>
        <div
          style={{
            backgroundColor: 'rgba(255,249,240,0.9)',
            borderRadius: 999,
            boxShadow: '0 6px 20px rgba(42,25,18,0.18)',
            color: palette.accent,
            fontSize: 24,
            fontWeight: 800,
            padding: '12px 19px',
          }}
        >
          {props.cefr}
        </div>
      </div>

      <div
        style={{
          backgroundColor: 'rgba(255,249,240,0.91)',
          border: '2px solid rgba(255,255,255,0.7)',
          borderRadius: 42,
          boxShadow: '0 26px 70px rgba(43,25,18,0.3)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          left: 62,
          minHeight: hookActive ? 430 : 500,
          padding: '54px 52px 58px',
          position: 'absolute',
          right: 62,
          top: hookActive ? 600 : 690,
        }}
      >
        {!hookActive && !promptActive && !answerActive && activeScene ? (
          <SpeakerChip speaker={activeScene.speaker} accent={palette.accent} />
        ) : null}
        <div
          style={{
            color: palette.accent,
            fontSize: 25,
            fontWeight: 850,
            letterSpacing: 1.2,
            marginBottom: 25,
          }}
        >
          {eyebrow} · {formatLabels[props.format]}
        </div>
        <div
          style={{
            fontFamily: 'Georgia, Times New Roman, serif',
            fontSize: hookActive || promptActive ? 67 : answerActive ? 59 : 55,
            fontWeight: 700,
            letterSpacing: -1.25,
            lineHeight: 1.18,
            opacity: hookActive ? 1 : entrance,
            transform: hookActive
              ? `scale(${hookScale})`
              : `translateY(${interpolate(entrance, [0, 1], [20, 0])}px)`,
          }}
        >
          {mainText}
        </div>
        {promptActive ? (
          <div style={{color: palette.accent, fontSize: 27, fontWeight: 750, marginTop: 34}}>
            Pause and say your answer aloud.
          </div>
        ) : null}
      </div>

      <div
        style={{
          alignItems: 'center',
          bottom: 92,
          display: 'flex',
          flexDirection: 'column',
          left: 62,
          opacity: ctaActive ? interpolate(second, [props.durationSec - 3.5, props.durationSec - 3], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 0,
          position: 'absolute',
          right: 62,
        }}
      >
        <div
          style={{
            backgroundColor: palette.paper,
            borderRadius: 999,
            boxShadow: '0 12px 34px rgba(42,25,18,0.28)',
            color: palette.accent,
            fontFamily: 'Georgia, serif',
            fontSize: 30,
            fontWeight: 700,
            padding: '18px 34px',
          }}
        >
          {props.cta}
        </div>
      </div>

      <div
        style={{
          backgroundColor: 'rgba(255,249,240,0.32)',
          bottom: 42,
          height: 5,
          left: 62,
          overflow: 'hidden',
          position: 'absolute',
          right: 62,
        }}
      >
        <div style={{backgroundColor: '#FFF7EA', height: '100%', width: progress}} />
      </div>
    </AbsoluteFill>
  );
};
