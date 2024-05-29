import BrowserFetch from './browserFetch';
import NodeFetch from './nodeFetch';
import {getCurrentEnvironment} from '../utils';

let Fetch;
if (getCurrentEnvironment() === 'browser') {
    Fetch = BrowserFetch;
}
else {
    Fetch = NodeFetch;
}
export interface FetchConfig {
    retries: number;
    timeout: number;
    backoffFactor?: number | undefined;
    retryMaxWaitInterval: number | undefined;
}
export default Fetch;