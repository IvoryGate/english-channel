import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const palette = {
  ink: '#3c281d',
  line: '#8e614c',
  paper: '#f5eedf',
  rose: '#b97772',
  cream: '#fffaf0',
  softRose: '#f1d5cc',
};

const Spark = ({index, x, y, size = 36}: {index: number; x: number; y: number; size?: number}) => {
  const frame = useCurrentFrame();
  const delay = 18 + index * 11;
  const opacity = interpolate(frame, [delay, delay + 11, 246, 270], [0, 0.82, 0.82, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const scale = spring({fps: 30, frame: Math.max(0, frame - delay), config: {damping: 12, stiffness: 180}});
  const drift = Math.sin((frame + index * 22) / 15) * 9;

  return (
    <svg
      viewBox="0 0 36 36"
      style={{
        position: 'absolute',
        width: size,
        height: size,
        left: x,
        top: y + drift,
        opacity,
        transform: `scale(${scale}) rotate(${frame * 1.1}deg)`,
      }}
    >
      <path d="M18 0 L21.5 14.5 L36 18 L21.5 21.5 L18 36 L14.5 21.5 L0 18 L14.5 14.5 Z" fill={palette.rose} />
    </svg>
  );
};

const BookMark = () => {
  const frame = useCurrentFrame();
  const rise = Math.sin(frame / 18) * 7;
  return (
    <svg viewBox="0 0 90 72" style={{position: 'absolute', left: 665, top: 732 + rise, width: 90, opacity: 0.72}}>
      <path d="M4 11 C19 5 31 8 45 19 V60 C31 49 19 46 4 52 Z M86 11 C71 5 59 8 45 19 V60 C59 49 71 46 86 52 Z" fill="none" stroke={palette.line} strokeWidth="3" strokeLinejoin="round" />
      <path d="M45 19 V60" stroke={palette.line} strokeWidth="3" />
    </svg>
  );
};

export const EnglishListeningRoomIntro = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const avatarIn = spring({fps, frame, config: {damping: 17, stiffness: 90, mass: 0.8}});
  const welcomeIn = spring({fps, frame: Math.max(0, frame - 18), config: {damping: 18, stiffness: 105}});
  const titleIn = spring({fps, frame: Math.max(0, frame - 42), config: {damping: 17, stiffness: 90}});
  const practiceIn = spring({fps, frame: Math.max(0, frame - 91), config: {damping: 16, stiffness: 105}});
  const subscribeIn = spring({fps, frame: Math.max(0, frame - 160), config: {damping: 14, stiffness: 120}});
  const lineProgress = interpolate(frame, [3, 36], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const fadeOut = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const avatarScale = interpolate(avatarIn, [0, 1], [0.79, 1]);
  const avatarY = interpolate(avatarIn, [0, 1], [86, 0]) + Math.sin(frame / 21) * 7;
  const avatarTilt = Math.sin(frame / 28) * 1.2;
  const welcomeY = interpolate(welcomeIn, [0, 1], [28, 0]);
  const titleY = interpolate(titleIn, [0, 1], [40, 0]);
  const practiceY = interpolate(practiceIn, [0, 1], [32, 0]);
  const subscribeY = interpolate(subscribeIn, [0, 1], [38, 0]);
  const rimTurn = interpolate(frame, [0, durationInFrames], [0, 12]);
  const pulse = 1 + Math.max(0, Math.sin((frame - 175) / 7)) * 0.045;
  const showPractice = interpolate(frame, [84, 100, 153, 170], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const showSubscribe = interpolate(frame, [156, 174, durationInFrames - 18, durationInFrames], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill
      style={{
        backgroundColor: palette.paper,
        backgroundImage:
          'radial-gradient(circle at 12% 13%, rgba(255,255,255,.9) 0 1px, transparent 1.5px), radial-gradient(circle at 80% 70%, rgba(60,40,29,.04) 0 1px, transparent 1.5px), linear-gradient(130deg, #fbf5e9 0%, #f3ead9 100%)',
        backgroundSize: '13px 13px, 19px 19px, 100% 100%',
        opacity: fadeOut,
        overflow: 'hidden',
      }}
    >
      <Audio src={staticFile('branding/english-listening-room-welcome.wav')} />
      <div style={{position: 'absolute', left: -120, top: -200, width: 840, height: 840, border: `2px solid ${palette.line}`, borderRadius: '50%', opacity: 0.22}} />
      <div style={{position: 'absolute', left: -35, top: -115, width: 670, height: 670, border: `1px solid ${palette.line}`, borderRadius: '50%', opacity: 0.25}} />
      <div style={{position: 'absolute', left: 110, top: 870, width: 720, height: 170, background: 'radial-gradient(ellipse, rgba(104,65,44,.18) 0%, transparent 67%)', filter: 'blur(12px)'}} />

      <svg viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
        <path d="M770 313 C 1015 230, 1290 222, 1705 313" fill="none" stroke={palette.line} strokeWidth="3" strokeLinecap="round" style={{strokeDasharray: 1200, strokeDashoffset: 1200 * (1 - lineProgress)}} />
        <path d="M770 771 C 1015 855, 1290 860, 1705 771" fill="none" stroke={palette.line} strokeWidth="3" strokeLinecap="round" style={{strokeDasharray: 1200, strokeDashoffset: 1200 * (1 - lineProgress)}} />
      </svg>

      <div style={{position: 'absolute', left: 208, top: 207, transform: `translateY(${avatarY}px) scale(${avatarScale}) rotate(${avatarTilt}deg)`, width: 590, height: 590, borderRadius: '50%', padding: 17, background: palette.cream, boxShadow: '0 24px 45px rgba(69,43,30,.17)'}}>
        <div style={{position: 'absolute', inset: 5, border: `2px dashed ${palette.rose}`, borderRadius: '50%', opacity: 0.75, transform: `rotate(${rimTurn}deg)`}} />
        <div style={{width: '100%', height: '100%', borderRadius: '50%', overflow: 'hidden', border: `2px solid ${palette.line}`, position: 'relative'}}>
          <Img src={staticFile('branding/english_listening_room_avatar_v2.png')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          <div style={{position: 'absolute', inset: 0, background: `linear-gradient(${130 + frame * 1.4}deg, transparent 42%, rgba(255,255,255,.3) 50%, transparent 58%)`, mixBlendMode: 'screen', opacity: 0.6}} />
        </div>
      </div>
      <BookMark />

      <div style={{position: 'absolute', left: 925, top: 307, color: palette.ink}}>
        <div style={{fontFamily: 'Georgia, serif', fontSize: 39, letterSpacing: 6, fontWeight: 700, color: palette.line, marginBottom: 19, opacity: welcomeIn, transform: `translateY(${welcomeY}px)`}}>HI, WELCOME TO</div>
        <div style={{fontFamily: 'Georgia, serif', fontSize: 88, lineHeight: 0.98, fontWeight: 700, letterSpacing: -2, opacity: titleIn, transform: `translateY(${titleY}px)`}}>English</div>
        <div style={{fontFamily: 'Georgia, serif', fontSize: 88, lineHeight: 1.03, fontWeight: 700, letterSpacing: -2, opacity: titleIn, transform: `translateY(${titleY}px)`}}>Listening Room</div>
        <div style={{width: 137, height: 5, marginTop: 34, backgroundColor: palette.rose, borderRadius: 3, transform: `scaleX(${titleIn})`, transformOrigin: 'left'}} />

        <div style={{position: 'absolute', top: 350, left: 0, display: 'flex', gap: 15, opacity: showPractice, transform: `translateY(${practiceY}px)`}}>
          {['LISTEN', 'NOTICE', 'SPEAK'].map((word, index) => (
            <div key={word} style={{padding: '12px 20px', borderRadius: 26, border: `2px solid ${index === 1 ? palette.rose : palette.line}`, backgroundColor: index === 1 ? palette.softRose : 'rgba(255,250,240,.65)', color: palette.ink, fontFamily: 'Georgia, serif', fontSize: 24, fontWeight: 700, letterSpacing: 2}}>{word}</div>
          ))}
        </div>

        <div style={{position: 'absolute', top: 340, left: 0, opacity: showSubscribe, transform: `translateY(${subscribeY}px) scale(${pulse})`, transformOrigin: 'left center', display: 'flex', alignItems: 'center', gap: 20}}>
          <div style={{padding: '17px 30px 18px', borderRadius: 34, backgroundColor: palette.rose, boxShadow: '0 10px 0 #8f554f, 0 17px 26px rgba(91,52,42,.2)', color: palette.cream, fontFamily: 'Georgia, serif', fontSize: 29, fontWeight: 700, letterSpacing: 2}}>SUBSCRIBE</div>
          <div style={{fontFamily: 'Georgia, serif', fontSize: 29, color: palette.line, fontStyle: 'italic'}}>Join the room <span style={{fontStyle: 'normal'}}>✦</span></div>
        </div>
      </div>

      <Spark index={0} x={824} y={277} />
      <Spark index={1} x={1600} y={309} size={33} />
      <Spark index={2} x={1515} y={785} size={28} />
      <Spark index={3} x={775} y={798} size={22} />
    </AbsoluteFill>
  );
};
