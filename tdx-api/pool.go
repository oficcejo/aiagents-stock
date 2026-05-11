package tdx

import (
	"errors"
	"github.com/injoyai/base/safe"
)

// NewPool 简易版本的连接池
func NewPool(dial func() (*Client, error), number int) (*Pool, error) {
	if number <= 0 {
		number = 1
	}
	ch := make(chan *Client, number)
	p := &Pool{
		ch: ch,
		Closer: safe.NewCloser().SetCloseFunc(func(err error) error {
			close(ch)
			return nil
		}),
	}
	for i := 0; i < number; i++ {
		c, err := dial()
		if err != nil {
			return nil, err
		}
		p.ch <- c
	}
	return p, nil
}

type Pool struct {
	ch chan *Client
	*safe.Closer
}

func (this *Pool) Get() (*Client, error) {
	select {
	case <-this.Done():
		return nil, this.Err()
	case c, ok := <-this.ch:
		if !ok {
			return nil, errors.New("已关闭")
		}
		return c, nil
	}
}

func (this *Pool) Put(c *Client) {
	select {
	case <-this.Done():
		c.Close()
		return
	case this.ch <- c:
	}
}

func (this *Pool) Do(fn func(c *Client) error) error {
	c, err := this.Get()
	if err != nil {
		return err
	}
	defer this.Put(c)
	return fn(c)
}

func (this *Pool) Go(fn func(c *Client)) error {
	c, err := this.Get()
	if err != nil {
		return err
	}
	go func(c *Client) {
		defer this.Put(c)
		fn(c)
	}(c)
	return nil
}
