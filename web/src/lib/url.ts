// base 경로(/fab-atlas)를 붙여 내부 링크를 만들어요.
export function withBase(path = ''): string {
	const base = import.meta.env.BASE_URL.replace(/\/$/, '');
	const clean = path.replace(/^\//, '');
	return `${base}/${clean}`;
}
