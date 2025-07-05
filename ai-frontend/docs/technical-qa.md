# AI-Frontend Technical Q&A

## Architecture & Integration Questions

### Claude Code CLI Integration
1. How should ai-frontend invoke Claude Code CLI? Should it use subprocess calls, or is there a Python API/SDK available?
decide whats better
2. What's the exact command format for invoking Claude Code CLI with context (schema, existing components, etc.)?
decide whats better
3. Should we pass the entire database schema to Claude Code on every request, or maintain a context file?
claude code can access files, you can pipe, etc. read docs on the internet, decide
4. How do we handle Claude Code's interactive prompts programmatically?
decide
5. Should we use Claude Code's --resume feature for iterative component updates?
decide

### Component Generation Strategy
1. Should we generate one component per request, or can users request multiple components in a single operation?
multiple. generally you need to keep working until claude code says everything is good, and it needs to be instructed to compile the frontend, and you need to compile it too to validate. only after that everything's good. in the config - some iterations limit (best practices for python library), and raise an error if failure.
2. What's the preferred component structure? (e.g., /components/[feature]/[ComponentName].tsx)
up to you
3. Should we generate separate files for styles, or use CSS-in-JS solutions like styled-components or emotion?
up to you, but needs to be easy. only best practices for our use case (code generation). simplicity. proabbly dont need much styles. at least for poc.
4. Do we need to generate Storybook stories alongside components?
not sure what that is, probably not. not sure. decide please. it's poc
5. Should components be generated as functional components with hooks exclusively?
you decide whats better on the longer run

### TypeScript & Type Generation
1. Should we generate a central types file from the AI-DB schema, or co-locate types with components?
up to you, what will work better
2. How should we handle nullable fields and optional relationships in TypeScript types?
up to you, whats better
3. Should we generate Zod schemas for runtime validation alongside TypeScript types?
up to you, whats better
4. What naming convention for generated types? (e.g., IUser, User, UserType, UserModel)?
up to you, whats better

### Data Fetching & State Management
1. What data fetching approach should we use? (React Query, SWR, RTK Query, custom hooks?)
calling the ai-db free-language query!
2. Should we generate GraphQL queries/mutations or REST API calls?
assume it'll be hosted somewhere. basically for views - a compiled function, for edits - freetext query. ai-db. probably api will be hosted somewhere, assume it. it'll probably be another component and docker-compose.
3. How does the frontend communicate with AI-DB? Is there an API server, or direct library calls?
api server
4. Should we implement optimistic updates for better UX?
not sure what it means. for better ux? probably yes, ux is very important
5. What state management solution? (Context API, Redux, Zustand, Jotai?)
up to you, but keep in mind code is generated, it needs to be simple and predictable for claude-code, and as little inter-pages dependencies as possible, hmm. up to you what you think is best. probably go with the most standard and expected

### Voice & Gesture Input
1. Which Web Speech API features should we use for voice input?
dont do voice for now
2. Should voice commands be processed locally or sent to Claude Code for interpretation?
3. For pointing gestures, should we use click events, or more advanced gesture recognition?
4. How do we correlate voice input with pointed elements? (e.g., "make this bigger" while clicking)
5. Should we show visual feedback during voice recording?

### Chrome MCP Integration
1. What specific visual context should we capture from Chrome? (screenshots, DOM structure, computed styles?)
use pupeeter mcp or there's a microsoft mcp that runs chrome and allows agents to control it, see visual, read console, etc
2. How does the Chrome MCP extension communicate with ai-frontend?
it communicates with claude. claude needs to be setup to use that mcp. assume you'll be in docker if that's easier for you. you can create dockerfiles.
3. Should we support selecting elements in Chrome to modify them via ai-frontend?
not sure what it means
4. What's the data format for passing visual context to Claude Code?
it's mcp, built in, between claude code and mcp. you see, claude code needs to see the results of his work. it'll iterate and finish and result will be very good.

### Design System & Styling
1. Should we use an existing component library (Material-UI, Ant Design, Chakra UI) as a base?
the most standard one, and good for our analytics.
2. If custom design system, what CSS approach? (CSS Modules, styled-components, Tailwind, vanilla CSS?)
up to you, most standard
3. Should we generate a theme configuration file?
up to you, most standard
4. How do we ensure consistent spacing, colors, and typography across generated components?
up to you, most standard
5. Should dark mode support be included by default?
no

### Documentation Generation
1. What format for component documentation? (MDX, Markdown, JSDoc comments?)
up to you, most standard
2. Should we generate API documentation for component props?
there should be a semantic file explaining everything, generated by ai. claude code should be instructed to do that. separate api docs - no, and you're not doing an api. you're generating typescript sources that compile to static files.
3. Where should documentation be stored relative to components?
n/a
4. Should we generate usage examples automatically?
nooo
5. Do we need to generate architecture diagrams?
no

### Build & Development Setup
1. What React version should we target?
up to you, whats best
2. Should we use Vite, Next.js, Create React App, or another build tool?
up to you, whats best, easiest for claude to work with, and overall stable and easy
3. Do we need server-side rendering (SSR) or static site generation (SSG)?
ssg
4. What testing framework for generated components? (Jest, Vitest, React Testing Library?)
maybe not needed? compilation (linting etc) + claude code vision
5. Should we generate test files alongside components?
not in the poc, no testing like that

### Error Handling & Validation
1. How should we handle AI-DB query errors in the UI?
error popup, something standard ux
2. Should we generate error boundary components?
up to you, whats best for our case
3. What level of client-side validation for forms?
ai will decide, it's not you who generates them I think. dont include claude code instructions that you're not sure about, let it decide. just describe the env and the task for him
4. How do we handle and display constraint violations from AI-DB?
same
5. Should we implement retry logic for failed requests?
yes

### Performance & Optimization
1. Should we implement code splitting by default?
up to you, whats best for our case
2. How do we handle large datasets? (virtualization, pagination, infinite scroll?)
pagination or whats easy. generally claude code will decide, it's not you
3. Should we generate React.memo wrapped components for performance?
4. What image optimization strategy?
5. Should we implement Progressive Web App (PWA) features?
no

### Security Considerations
1. How do we handle authentication and authorization in generated components?
no
2. Should we sanitize user inputs in forms?
no
3. What CORS configuration is needed for AI-DB communication?
none, it's not you who implement the api
4. How do we handle sensitive data display (masking, encryption)?
n/a
5. Should we implement CSP (Content Security Policy) headers?
you dont do api

### Transaction Support
1. How do we show transaction status in the UI during git-layer operations?
umm whats best ux practice
2. Should we generate preview components for uncommitted changes?
you're not an interface of schema modifications. it's the console who will, or some admin tool who will. you're just a library which invokes claude code, knows how to work in a transaction by git-layer, and that's it. you provide the source code files and compile those files, and thats where your job is over. in the directory provided by git layer. your ui is a skeleton that you generate, and claude code will take care of components. you need to make sure claude code doesnt break the skeleton, its changes are isolated (google docs how to use it and give it right privileges by command line switches, its the cli). you need to compile and validate the generated sources by claude code.
3. How do we handle UI updates when transactions are rolled back?
it's not a ui of updating the schema. if you're asking about data modification transactions (user inputs an entry to the db via the ui generated by claude code), - best ux practice. progress, etc. messages popups etc.
4. Should we show a diff view for pending changes?
no
5. Do we need conflict resolution UI for concurrent edits?
nooo, n/a

### Development Workflow
1. Should we generate a development server that auto-reloads on AI-DB schema changes?
no
2. How do we handle hot module replacement (HMR) for generated components?
we dont, user will have to refresh
3. Should we create npm scripts for common ai-frontend operations?
not sure what you mean
4. Do we need a CLI interface for ai-frontend, or is it purely library-based?
not sure what you mean, probably n/a
5. How do we handle environment variables and configuration?
standard python library config.

### Deployment & Distribution
1. Should generated frontends be self-contained (include all dependencies)?
yep
2. What's the build output structure?
ummmm files? :)
3. Should we generate Docker configurations?
for you (the python lib) and the claude-code, if you feel you need to. not for the frontends.
4. Do we need to support CDN deployment?
no
5. How do we handle API endpoint configuration for different environments?
it's not you

### Versioning & Compatibility
1. How do we handle breaking changes in AI-DB schema?
they won't reach you
2. Should we version generated components?
no, git-layer will take care
3. What's the migration strategy for existing frontends when schema changes?
when db schema changes... the strategy is to call you. and you'll call claude code. and validate in the end. optionally it'll return errors or re-ask something and you'll raise an error saying something is missing, need info, cant be done, etc. and they'll have to specify it and re-query you. but you don't handle the dialog. you're just a func.
4. Should we maintain backwards compatibility with older AI-DB versions?
no
5. How do we track which frontend version works with which schema version?
we dont

### Additional Technical Considerations
1. Should we support internationalization (i18n) in generated components?
not in the poc
2. Do we need real-time updates via WebSockets or Server-Sent Events?
no
3. Should we generate OpenAPI/Swagger documentation?
n/a
4. What browser versions should we support?
chrome
5. Do we need offline functionality support?
no
6. Should components be generated with analytics tracking hooks?
no
7. How do we handle file uploads and media management?
n/a
8. Should we support drag-and-drop interfaces?
claude code will decide
9. What accessibility standards should we target (WCAG 2.1 AA)?
umm whats easier
10. Do we need to generate admin interfaces separately from user-facing components?
YOU generate only user-facing components (and actually not you, it's claude. you call it, and generate the skeleton - not modifyable by claude code, but loading and showing components, menu, etc. menu - lets be dynamic for now. or allow claude code to modify it. yes.)