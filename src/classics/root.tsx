import {Composition} from 'remotion';
import {ClassicListeningCard} from './classic-listening-card';
import {PersuasionChapterCover} from './persuasion-chapter-cover';

const voice = (chapter: number, mode: 'intro' | 'outro') => `branding/chapter-${String(chapter).padStart(2, '0')}-${mode}.wav`;

export const ClassicsRoot = () => (
  <>
    {([1, 2, 3] as const).flatMap((chapter) => [
      <Composition
        key={`intro-${chapter}`}
        id={`PersuasionChapter${chapter}Intro`}
        component={ClassicListeningCard}
        defaultProps={{mode: 'intro' as const, chapter, voiceFile: voice(chapter, 'intro')}}
        durationInFrames={300}
        fps={30}
        width={2560}
        height={1440}
      />,
      <Composition
        key={`outro-${chapter}`}
        id={`PersuasionChapter${chapter}Outro`}
        component={ClassicListeningCard}
        defaultProps={{mode: 'outro' as const, chapter, voiceFile: voice(chapter, 'outro')}}
        durationInFrames={330}
        fps={30}
        width={2560}
        height={1440}
      />,
      <Composition
        key={`cover-${chapter}`}
        id={`PersuasionChapter${chapter}Cover`}
        component={PersuasionChapterCover}
        defaultProps={{chapter}}
        durationInFrames={1}
        fps={30}
        width={2560}
        height={1440}
      />,
    ])}
  </>
);
