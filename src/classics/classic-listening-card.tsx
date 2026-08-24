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

type Props = {mode: 'intro' | 'outro'; chapter: 1 | 2 | 3; voiceFile: string};

const chapterWord = (chapter: number) => ({1: 'ONE', 2: 'TWO', 3: 'THREE', 4: 'FOUR'}[chapter] ?? String(chapter));

const serif = 'Georgia, Times New Roman, serif';
const ink = '#442d22';
const mahogany = '#6d4031';
const gold = '#c3974c';
const rose = '#b36e6a';
const ivory = '#fff9e9';

const bounded = (frame: number, input: [number, number], output: [number, number]) =>
  interpolate(frame, input, output, {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

const fadeWindow = (frame: number, enter: number, hold: number, exit: number) =>
  interpolate(frame, [enter, enter + 15, hold, exit], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

const InkLine = ({start, width, top, left}: {start: number; width: number; top: number; left: number}) => {
  const frame = useCurrentFrame();
  const progress = spring({fps: 30, frame: Math.max(0, frame - start), config: {damping: 22, stiffness: 42}});
  return (
    <svg viewBox="0 0 1000 48" style={{position: 'absolute', left, top, width, height: 48, overflow: 'visible'}}>
      <path
        d="M8 25 C180 7 342 42 506 23 C674 4 824 34 992 17"
        fill="none"
        stroke={gold}
        strokeWidth="6"
        strokeLinecap="round"
        pathLength="1"
        strokeDasharray="1"
        strokeDashoffset={1 - progress}
        opacity={0.92}
      />
      <path
        d="M38 36 C220 23 349 48 520 34 C696 18 824 45 954 29"
        fill="none"
        stroke={rose}
        strokeWidth="2"
        strokeLinecap="round"
        pathLength="1"
        strokeDasharray="1"
        strokeDashoffset={1 - progress}
        opacity={0.58}
      />
    </svg>
  );
};

const RevealedText = ({
  children,
  start,
  style,
  distance = 38,
}: {
  children: string;
  start: number;
  style: React.CSSProperties;
  distance?: number;
}) => {
  const frame = useCurrentFrame();
  const progress = spring({fps: 30, frame: Math.max(0, frame - start), config: {damping: 20, stiffness: 62}});
  return (
    <div style={{overflow: 'hidden', ...style}}>
      <div
        style={{
          transform: `translateY(${bounded(progress, [0, 1], [distance, 0])}px)`,
          clipPath: `inset(0 ${100 - progress * 100}% 0 0)`,
          opacity: progress,
        }}
      >
        {children}
      </div>
    </div>
  );
};

const LetterTitle = ({text, start, style}: {text: string; start: number; style: React.CSSProperties}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{display: 'flex', ...style}}>
      {Array.from(text).map((letter, index) => {
        const progress = spring({
          fps: 30,
          frame: Math.max(0, frame - start - index * 2.3),
          config: {damping: 19, stiffness: 70},
        });
        return (
          <span
            key={`${letter}-${index}`}
            style={{
              display: 'inline-block',
              minWidth: letter === ' ' ? 32 : undefined,
              opacity: progress,
              transform: `translateY(${bounded(progress, [0, 1], [54, 0])}px) rotate(${bounded(progress, [0, 1], [-2.2, 0])}deg)`,
              filter: `blur(${bounded(progress, [0, 1], [7, 0])}px)`,
            }}
          >
            {letter === ' ' ? '\u00a0' : letter}
          </span>
        );
      })}
    </div>
  );
};

const ActionCue = ({start, mode, chapter}: {start: number; mode: 'intro' | 'outro'; chapter: number}) => {
  const frame = useCurrentFrame();
  const entrance = spring({fps: 30, frame: Math.max(0, frame - start), config: {damping: 19, stiffness: 58}});
  const line = spring({fps: 30, frame: Math.max(0, frame - start - 14), config: {damping: 22, stiffness: 44}});
  const pulse = 1 + Math.max(0, Math.sin((frame - start - 22) / 13)) * 0.035;
  const intro = mode === 'intro';
  return (
    <div
      style={{
        position: 'absolute',
        left: intro ? 1570 : 115,
        bottom: intro ? 82 : 72,
        width: intro ? 820 : 1240,
        display: 'flex',
        alignItems: 'center',
        gap: 30,
        opacity: entrance,
        transform: `translateY(${bounded(entrance, [0, 1], [58, 0])}px)`,
      }}
    >
      <div
        style={{
          width: 108,
          height: 108,
          flex: '0 0 108px',
          borderRadius: '50%',
          display: 'grid',
          placeItems: 'center',
          background: rose,
          border: `5px solid ${ivory}`,
          outline: `3px solid ${gold}`,
          boxShadow: '0 15px 34px rgba(92,51,35,.24)',
          transform: `scale(${pulse})`,
        }}
      >
        <svg viewBox="0 0 64 64" style={{width: 48, height: 48, marginLeft: 6}}>
          <path d="M18 10 L52 32 L18 54Z" fill={ivory} />
        </svg>
      </div>
      <div style={{flex: 1}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
          <div style={{fontFamily: serif, fontSize: 25, letterSpacing: 7, color: mahogany, fontWeight: 700}}>
            {intro ? 'READY WHEN YOU ARE' : 'KEEP THE STORY GOING'}
          </div>
          <div style={{height: 3, width: bounded(line, [0, 1], [0, intro ? 175 : 310]), background: gold}} />
        </div>
        <div style={{fontFamily: serif, fontSize: intro ? 48 : 50, lineHeight: 1.1, marginTop: 11, color: ink, fontWeight: 700}}>
          {intro ? `BEGIN CHAPTER ${chapterWord(chapter)}` : 'SUBSCRIBE AND CONTINUE'}
        </div>
      </div>
    </div>
  );
};

const FloatingLight = () => {
  const frame = useCurrentFrame();
  return (
    <>
      {Array.from({length: 20}).map((_, index) => {
        const baseX = 90 + ((index * 421) % 2400);
        const baseY = 80 + ((index * 193) % 1260);
        const radius = 3 + (index % 4);
        return (
          <div
            key={index}
            style={{
              position: 'absolute',
              left: baseX + Math.sin((frame + index * 19) / 42) * 18,
              top: baseY - ((frame * (0.12 + (index % 3) * 0.03)) % 160),
              width: radius,
              height: radius,
              borderRadius: '50%',
              background: '#fff2bf',
              boxShadow: '0 0 16px rgba(255,230,153,.8)',
              opacity: 0.18 + Math.max(0, Math.sin((frame + index * 13) / 27)) * 0.25,
            }}
          />
        );
      })}
    </>
  );
};

const AvatarHero = ({mode}: {mode: 'intro' | 'outro'}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const entrance = spring({fps, frame: Math.max(0, frame - 5), config: {damping: 19, stiffness: 54}});
  const isIntro = mode === 'intro';
  const left = isIntro ? 90 : 1720;
  const top = isIntro ? 330 : 315;
  const size = isIntro ? 760 : 750;
  const translateX = bounded(entrance, [0, 1], [isIntro ? -180 : 180, 0]);
  const slowFloat = Math.sin(frame / 34) * 8;
  return (
    <div style={{position: 'absolute', left, top, width: size, height: size}}>
      <div
        style={{
          position: 'absolute',
          inset: -100,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255,250,229,.96) 0%, rgba(255,225,165,.48) 46%, transparent 72%)',
          filter: 'blur(7px)',
          opacity: entrance,
        }}
      />
      <svg viewBox="0 0 800 800" style={{position: 'absolute', inset: -20, width: size + 40, height: size + 40, transform: `rotate(${frame / 19}deg)`, opacity: entrance * 0.7}}>
        <circle cx="400" cy="400" r="382" fill="none" stroke={gold} strokeWidth="3" strokeDasharray="8 18" />
        <circle cx="400" cy="400" r="366" fill="none" stroke={rose} strokeWidth="2" strokeDasharray="2 22" />
      </svg>
      <div
        style={{
          position: 'absolute',
          inset: 16,
          borderRadius: '50%',
          padding: 13,
          background: ivory,
          border: `5px solid ${gold}`,
          boxShadow: '0 35px 78px rgba(84,48,29,.30)',
          opacity: entrance,
          transform: `translateX(${translateX}px) translateY(${slowFloat}px) scale(${bounded(entrance, [0, 1], [0.8, 1])})`,
        }}
      >
        <Img
          src={staticFile('branding/english_listening_room_avatar_v2.png')}
          style={{width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%'}}
        />
      </div>
    </div>
  );
};

const IntroSequence = ({chapter}: {chapter: number}) => {
  const frame = useCurrentFrame();
  const welcomeOpacity = fadeWindow(frame, 14, 104, 128);
  const titleShift = bounded(frame, [106, 138], [0, -78]);
  const classicIn = spring({fps: 30, frame: Math.max(0, frame - 72), config: {damping: 20, stiffness: 55}});
  const chapterIn = spring({fps: 30, frame: Math.max(0, frame - 202), config: {damping: 18, stiffness: 64}});
  return (
    <>
      <AvatarHero mode="intro" />
      <div style={{position: 'absolute', left: 900, top: 245, width: 1500, color: ink}}>
        <div style={{opacity: welcomeOpacity, transform: `translateY(${titleShift}px)`}}>
          <RevealedText
            start={15}
            style={{fontFamily: serif, fontSize: 44, letterSpacing: 14, fontWeight: 700, color: mahogany}}
          >
            WELCOME TO
          </RevealedText>
          <RevealedText
            start={28}
            style={{fontFamily: serif, fontSize: 84, lineHeight: 1.05, letterSpacing: 2, fontWeight: 700, marginTop: 18}}
          >
            ENGLISH LISTENING ROOM
          </RevealedText>
        </div>

        <div style={{position: 'absolute', top: 225, left: 0, opacity: classicIn, transform: `translateY(${bounded(classicIn, [0, 1], [42, 0])}px)`}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 28}}>
            <div style={{width: bounded(classicIn, [0, 1], [0, 190]), height: 5, background: gold}} />
            <div style={{fontFamily: serif, fontSize: 49, letterSpacing: 15, fontWeight: 700, color: rose}}>CLASSIC LISTENING</div>
          </div>
        </div>

        <LetterTitle
          text="PERSUASION"
          start={132}
          style={{position: 'absolute', top: 395, left: -8, fontFamily: serif, fontSize: 166, lineHeight: 1, letterSpacing: 4, fontWeight: 700, color: ink, textShadow: '0 3px 0 rgba(255,255,255,.7)'}}
        />
        <RevealedText
          start={174}
          style={{position: 'absolute', top: 590, left: 4, fontFamily: serif, fontSize: 48, fontStyle: 'italic', color: mahogany}}
        >
          By Jane Austen
        </RevealedText>
        <div
          style={{
            position: 'absolute',
            top: 700,
            left: 0,
            display: 'flex',
            alignItems: 'center',
            gap: 28,
            opacity: chapterIn,
            transform: `translateX(${bounded(chapterIn, [0, 1], [64, 0])}px)`,
          }}
        >
          <div style={{fontFamily: serif, fontSize: 38, letterSpacing: 10, fontWeight: 700, color: gold}}>CHAPTER</div>
          <div style={{fontFamily: serif, fontSize: 98, lineHeight: 1, fontWeight: 700, color: rose}}>{chapterWord(chapter)}</div>
          <div style={{width: bounded(chapterIn, [0, 1], [0, 260]), height: 3, background: gold}} />
        </div>
      </div>
      <InkLine start={93} width={1470} left={865} top={566} />
      <ActionCue start={202} mode="intro" chapter={chapter} />
    </>
  );
};

const OutroSequence = ({chapter}: {chapter: number}) => {
  const frame = useCurrentFrame();
  const continueIn = spring({fps: 30, frame: Math.max(0, frame - 82), config: {damping: 20, stiffness: 58}});
  const chapterIn = spring({fps: 30, frame: Math.max(0, frame - 150), config: {damping: 19, stiffness: 62}});
  const subscribeIn = spring({fps: 30, frame: Math.max(0, frame - 205), config: {damping: 20, stiffness: 58}});
  return (
    <>
      <AvatarHero mode="outro" />
      <div style={{position: 'absolute', left: 145, top: 215, width: 1510, color: ink}}>
        <RevealedText
          start={12}
          style={{fontFamily: serif, fontSize: 46, letterSpacing: 13, fontWeight: 700, color: mahogany}}
        >
          THANK YOU FOR LISTENING
        </RevealedText>
        <div style={{marginTop: 38, opacity: continueIn, transform: `translateY(${bounded(continueIn, [0, 1], [52, 0])}px)`}}>
          <div style={{fontFamily: serif, fontSize: 117, lineHeight: 1.03, fontWeight: 700}}>The story</div>
          <div style={{fontFamily: serif, fontSize: 117, lineHeight: 1.03, fontWeight: 700, fontStyle: 'italic', color: rose}}>continues.</div>
        </div>
        <div
          style={{
            marginTop: 55,
            display: 'flex',
            alignItems: 'baseline',
            gap: 34,
            opacity: chapterIn,
            transform: `translateX(${bounded(chapterIn, [0, 1], [-70, 0])}px)`,
          }}
        >
          <div style={{fontFamily: serif, fontSize: 36, letterSpacing: 9, fontWeight: 700, color: gold}}>PERSUASION</div>
          <div style={{fontFamily: serif, fontSize: 78, fontWeight: 700}}>CHAPTER {chapterWord(chapter + 1)}</div>
        </div>
        <div
          style={{
            marginTop: 65,
            width: 1170,
            paddingTop: 28,
            borderTop: `3px solid ${gold}`,
            opacity: subscribeIn,
            transform: `translateY(${bounded(subscribeIn, [0, 1], [34, 0])}px)`,
          }}
        >
          <div style={{fontFamily: serif, fontSize: 38, lineHeight: 1.35, letterSpacing: 4, fontWeight: 700, color: mahogany}}>
            ENGLISH LISTENING ROOM
          </div>
          <div style={{fontFamily: serif, fontSize: 34, marginTop: 14, fontStyle: 'italic', color: ink}}>
            More classics, warmly narrated.
          </div>
        </div>
      </div>
      <InkLine start={61} width={1390} left={112} top={395} />
      <ActionCue start={215} mode="outro" chapter={chapter} />
    </>
  );
};

export const ClassicListeningCard = ({mode, chapter, voiceFile}: Props) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const fade = interpolate(frame, [0, 10, durationInFrames - 14, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const background = mode === 'intro' ? 'classic-listening-intro-bg-v2.png' : 'classic-listening-outro-bg-v2.png';
  const panX = mode === 'intro' ? bounded(frame, [0, durationInFrames], [-12, 12]) : bounded(frame, [0, durationInFrames], [12, -12]);
  return (
    <AbsoluteFill style={{backgroundColor: '#f1d49d', color: ink, opacity: fade, overflow: 'hidden'}}>
      <Audio src={staticFile(`classics/persuasion/${voiceFile}`)} volume={1.2} />
      <Img
        src={staticFile(`classics/persuasion/${background}`)}
        style={{
          position: 'absolute',
          inset: -26,
          width: 'calc(100% + 52px)',
          height: 'calc(100% + 52px)',
          objectFit: 'cover',
          transform: `translateX(${panX}px) scale(${bounded(frame, [0, durationInFrames], [1.015, 1.045])})`,
        }}
      />
      <AbsoluteFill
        style={{
          background:
            mode === 'intro'
              ? 'linear-gradient(90deg, rgba(255,247,224,.18) 0%, rgba(255,248,228,.68) 31%, rgba(255,250,234,.92) 52%, rgba(255,246,221,.56) 100%)'
              : 'linear-gradient(90deg, rgba(255,248,228,.94) 0%, rgba(255,244,214,.80) 52%, rgba(104,65,43,.10) 100%)',
          boxShadow: 'inset 0 0 140px rgba(100,61,37,.18)',
        }}
      />
      <div style={{position: 'absolute', inset: 42, border: '3px solid rgba(185,137,62,.62)'}} />
      <div style={{position: 'absolute', inset: 58, border: '1px solid rgba(185,137,62,.40)'}} />
      <FloatingLight />
      {mode === 'intro' ? <IntroSequence chapter={chapter} /> : <OutroSequence chapter={chapter} />}
    </AbsoluteFill>
  );
};
