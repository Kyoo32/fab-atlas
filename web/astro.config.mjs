// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// 쇼케이스(/, /report/)는 src/pages, 작업노트(/notes/…)는 Starlight가 맡아요.
export default defineConfig({
	site: 'https://kyoo32.github.io',
	base: '/fab-atlas',
	trailingSlash: 'always',
	// 작업일지를 주제 단위로 합치면서 옮긴 옛 주소예요.
	redirects: {
		'/notes/devlog/2026-10-14-corpus-fill/': '/fab-atlas/notes/devlog/2026-10-13-corpus/',
	},
	integrations: [
		starlight({
			title: 'FabAtlas 작업노트',
			description: '8대 공정을 지도로 보고, 묻고, 근거로 답한다',
			locales: { root: { label: '한국어', lang: 'ko' } },
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/Kyoo32/fab-atlas' }],
			editLink: { baseUrl: 'https://github.com/Kyoo32/fab-atlas/edit/main/web/' },
			lastUpdated: true,
			sidebar: [
				{ label: '타임라인', link: '/notes/' },
				{ label: '작업일지', items: [{ autogenerate: { directory: 'notes/devlog' } }] },
				{ label: '용어사전', slug: 'notes/glossary' },
				{ label: '결정 기록', slug: 'notes/decisions' },
				{ label: '노트북', items: [{ autogenerate: { directory: 'notes/notebooks' } }] },
			],
		}),
	],
});
