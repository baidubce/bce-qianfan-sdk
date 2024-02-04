export const kEscapedMap: Record<string, string> = {
    '!': '%21',
    '\'': '%27',
    '(': '%28',
    ')': '%29',
    '*': '%2A'
};

export function normalize(string: string, encodingSlash?: boolean): string {
    let result = encodeURIComponent(string);
    result = result.replace(/[!'\(\)\*]/g, ($1) => kEscapedMap[$1]);

    if (encodingSlash === false) {
        result = result.replace(/%2F/gi, '/');
    }

    return result;
}

export function trim(string: string): string {
    return (string || '').replace(/^\s+|\s+$/g, '');
}

export function urlObjectToPlainObject(url: URL, httpMethod: string, headers: any): Record<string, string> {
    return {
      protocol: url.protocol,
      auth: url.username || (url.password ? '****:' : '') + url.password,
      host: url.host,
      port: url.port,
      hostname: url.hostname,
      hash: url.hash,
      search: url.search,
      query: url.searchParams.toString(),
      pathname: url.pathname,
      path: url.pathname + url.search,
      href: url.href,
      method: httpMethod,
      headers: headers
    };
}