package extend

import (
	"encoding/json"
	"fmt"
	"github.com/injoyai/conv"
	"github.com/injoyai/tdx"
	"io"
	"net/http"
	"path/filepath"
)

func ListenCodesHTTP(port int, filename ...string) error {
	code, err := tdx.DialCodes(conv.Default(filepath.Join(tdx.DefaultDatabaseDir, "codes.db"), filename...))
	if err != nil {
		return nil
	}
	return http.ListenAndServe(fmt.Sprintf(":%d", port), http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.RequestURI {
		case "/stocks":
			ls := code.GetStocks()
			w.WriteHeader(http.StatusOK)
			w.Write(conv.Bytes(ls))
		case "/etfs":
			ls := code.GetETFs()
			w.WriteHeader(http.StatusOK)
			w.Write(conv.Bytes(ls))
		default:
			http.NotFound(w, r)
		}
	}))
}

func DialCodesHTTP(address string) *CodesHTTP {
	return &CodesHTTP{address: address}
}

type CodesHTTP struct {
	address string
}

func (this *CodesHTTP) getList(path string) ([]string, error) {
	resp, err := http.DefaultClient.Get(this.address + path)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("http code:%d", resp.StatusCode)
	}
	bs, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	ls := []string(nil)
	err = json.Unmarshal(bs, &ls)
	return ls, err
}

func (this *CodesHTTP) GetStocks() ([]string, error) {
	return this.getList("/stocks")
}

func (this *CodesHTTP) GetETFs() ([]string, error) {
	return this.getList("/etfs")
}
